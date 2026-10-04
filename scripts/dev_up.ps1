# 论匠一键启动：PG → Redis → Ollama →（可选）后端 + 前端
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\dev_up.ps1              # 全栈（各开独立窗口）
#   powershell -ExecutionPolicy Bypass -File scripts\dev_up.ps1 -infra-only  # 只起 3 个依赖
#
# 幂等：端口已监听的服务自动跳过，重复执行不会重复启动、不会杀掉在跑的进程。
# 对称停止：scripts\dev_down.ps1

param(
    [switch]$infraOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# ===== 机器相关路径（换机器只改这里；留空则按常见位置自动探测）=====
$PgCtl    = ""    # pg_ctl.exe 完整路径，例：D:\Develop\DB\PostgreSQL16\Library\bin\pg_ctl.exe
$PgData   = ""    # PG 数据目录，例：D:\Develop\DB\PostgreSQL16\data
$RedisExe = "redis-server"   # Redis 可执行（在 PATH 里就用命令名）
$PyExe    = Join-Path $Root "envs\lunjiang\python.exe"

# ===== 工具函数 =====
function Test-Port {
    param([int]$Port)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        return ($async.AsyncWaitHandle.WaitOne(300) -and $client.Connected)
    } finally { $client.Close() }
}

function Resolve-PgPaths {
    # 变量区留空时自动探测 pg_ctl 与数据目录
    if ($PgCtl -and $PgData) { return }
    $candidates = @()
    if ($PgCtl) { $candidates += $PgCtl }
    else {
        $cmd = Get-Command pg_ctl -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
        $candidates += Get-ChildItem "D:\Develop\DB\PostgreSQL*\Library\bin\pg_ctl.exe" -ErrorAction SilentlyContinue
        $candidates += Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_ctl.exe" -ErrorAction SilentlyContinue
    }
    $candidates = $candidates | Where-Object { $_ }
    $found = $candidates | Select-Object -First 1
    if (-not $found) { return }
    if ($found -is [System.IO.FileInfo]) { $script:PgCtl = $found.FullName }
    elseif ($found.Source) { $script:PgCtl = $found.Source }
    else { $script:PgCtl = "$found" }
    if (-not $PgData) {
        # 数据目录约定：<安装根>\data（安装根 = ...\Library\bin 的上两级 或 ...\bin 的上一级）
        $bin = Split-Path -Parent $script:PgCtl
        $lib = Split-Path -Parent $bin
        if ((Split-Path -Leaf $lib) -eq "Library") {
            $script:PgData = Join-Path (Split-Path -Parent $lib) "data"
        } else {
            $script:PgData = Join-Path (Split-Path -Parent $bin) "data"
        }
    }
}

function Wait-Port {
    param([int]$Port, [string]$Name, [int]$Seconds = 15)
    for ($i = 0; $i -lt ($Seconds * 4); $i++) {
        if (Test-Port $Port) { Write-Host "  [OK] $Name 已监听 127.0.0.1:$Port" -ForegroundColor Green; return $true }
        Start-Sleep -Milliseconds 250
    }
    Write-Host "  [FAIL] $Name 在 ${Seconds}s 内未监听 $Port" -ForegroundColor Red
    return $false
}

Write-Host "== 论匠 dev_up ==" -ForegroundColor Cyan

# ===== 1) PostgreSQL =====
if (Test-Port 5433) {
    Write-Host "[SKIP] PostgreSQL 已在 5433 监听" -ForegroundColor Yellow
} else {
    Resolve-PgPaths
    if (-not $PgCtl -or -not (Test-Path $PgCtl)) {
        Write-Host "[FAIL] 找不到 pg_ctl：请在脚本顶部变量区填 \$PgCtl / \$PgData（或确认 PG 已安装）" -ForegroundColor Red
    } elseif (-not (Test-Path $PgData)) {
        Write-Host "[FAIL] 数据目录不存在：$PgData（检查 \$PgData 变量）" -ForegroundColor Red
    } else {
        Write-Host "[START] PostgreSQL（pg_ctl -D $PgData start）"
        & $PgCtl -D $PgData start 2>&1 | Out-Host
        if (-not (Wait-Port 5433 "PostgreSQL")) {
            Write-Host "       常见原因：异常退出残留 postmaster.pid —— 确认 5433 无监听、无 postgres 进程后删除 $PgData\postmaster.pid 再试（README FAQ）" -ForegroundColor DarkYellow
        }
    }
}

# ===== 2) Redis =====
if (Test-Port 6379) {
    Write-Host "[SKIP] Redis 已在 6379 监听" -ForegroundColor Yellow
} else {
    Write-Host "[START] Redis"
    Start-Process $RedisExe -WindowStyle Minimized -ErrorAction SilentlyContinue
    if (-not (Wait-Port 6379 "Redis")) {
        Write-Host "       若 redis-server 不在 PATH：注册为服务后 net start Redis，或修正脚本顶部 \$RedisExe" -ForegroundColor DarkYellow
    }
}

# ===== 3) Ollama =====
if (Test-Port 11434) {
    Write-Host "[SKIP] Ollama 已在 11434 监听" -ForegroundColor Yellow
} else {
    Write-Host "[START] Ollama serve"
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized -ErrorAction SilentlyContinue
    if (-not (Wait-Port 11434 "Ollama")) {
        Write-Host "       若未安装 Ollama：https://ollama.com 下载安装后再跑一次" -ForegroundColor DarkYellow
    }
}

if ($infraOnly) {
    Write-Host "`n== 依赖就绪。继续启动后端 + 前端：powershell -File scripts\dev_up.ps1 ==" -ForegroundColor Cyan
    exit 0
}

# ===== 4) 后端（新窗口）=====
if (Test-Port 8000) {
    Write-Host "[SKIP] 后端已在 8000 监听" -ForegroundColor Yellow
} elseif (-not (Test-Path $PyExe)) {
    Write-Host "[FAIL] 找不到 $PyExe —— 先完成 README 第 0 步（conda create + pip install）" -ForegroundColor Red
} else {
    Write-Host "[START] 后端 uvicorn（新窗口）"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$PyExe' -m uvicorn main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $Root
    Wait-Port 8000 "后端" 30 | Out-Null
}

# ===== 5) 前端（新窗口）=====
$FeDir = Join-Path $Root "frontend"
if (Test-Port 5173) {
    Write-Host "[SKIP] 前端已在 5173 监听" -ForegroundColor Yellow
} elseif (-not (Test-Path (Join-Path $FeDir "node_modules"))) {
    Write-Host "[FAIL] frontend\node_modules 不存在 —— 先完成 README 第 0 步（npm install）" -ForegroundColor Red
} else {
    Write-Host "[START] 前端 vite（新窗口）"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FeDir'; npm run dev"
    Wait-Port 5173 "前端" 30 | Out-Null
}

# ===== 6) 启动前快检（端口 + 模型 + .env，秒级）=====
if (Test-Path $PyExe) {
    Write-Host "`n== preflight 快检 ==" -ForegroundColor Cyan
    & $PyExe (Join-Path $PSScriptRoot "preflight.py")
} else {
    Write-Host "`n[提示] 虚拟环境不存在，跳过 preflight —— 先完成 README 第 0 步" -ForegroundColor DarkYellow
}

Write-Host "`n== 完成。打开 http://localhost:5173 使用；一键停止：powershell -File scripts\dev_down.ps1 ==" -ForegroundColor Cyan
