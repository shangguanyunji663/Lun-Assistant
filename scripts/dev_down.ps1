# 论匠一键停止：后端 → 前端 → PostgreSQL → Redis（Ollama 保持常驻）
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File scripts\dev_down.ps1                # 全部停止
#   powershell -ExecutionPolicy Bypass -File scripts\dev_down.ps1 -keep-infra    # 只停后端 + 前端，依赖留着
#
# 只停监听对应端口的进程，不碰其他进程。对称启动：scripts\dev_up.ps1

param(
    [switch]$keepInfra
)

$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot

# ===== 机器相关路径（与 dev_up.ps1 保持一致）=====
$PgData    = ""    # PG 数据目录，例：D:\Develop\DB\PostgreSQL16\data（留空自动探测）
$RedisCli  = "redis-cli"

# ===== 工具函数 =====
function Test-Port {
    param([int]$Port)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        return ($async.AsyncWaitHandle.WaitOne(300) -and $client.Connected)
    } finally { $client.Close() }
}

function Resolve-PgCtl {
    # 返回 pg_ctl.exe 路径；找不到返回 $null
    $cmd = Get-Command pg_ctl -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $found = Get-ChildItem "D:\Develop\DB\PostgreSQL*\Library\bin\pg_ctl.exe",
                            "C:\Program Files\PostgreSQL\*\bin\pg_ctl.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_ } | Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

function Resolve-PgData {
    # 由 pg_ctl 路径推数据目录：<安装根>\data（兼容 ...\Library\bin 与 ...\bin 两种布局）
    param([string]$PgCtlPath)
    $bin = Split-Path -Parent $PgCtlPath
    $parent = Split-Path -Parent $bin
    if ((Split-Path -Leaf $parent) -eq "Library") { return (Join-Path (Split-Path -Parent $parent) "data") }
    return (Join-Path $parent "data")
}

function Stop-PortListener {
    param([int]$Port, [string]$Name)
    if (-not (Test-Port $Port)) {
        Write-Host "[SKIP] $Name 未在运行（$Port 无监听）" -ForegroundColor Yellow
        return
    }
    $processIds = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($p in $processIds) {
        if ($p -and $p -ne $PID) {
            Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            Write-Host "[STOP] $Name（进程 $p，端口 $Port）" -ForegroundColor Green
        }
    }
}

Write-Host "== 论匠 dev_down ==" -ForegroundColor Cyan

# ===== 1) 后端 / 前端 =====
Stop-PortListener 8000 "后端 uvicorn"
Stop-PortListener 5173 "前端 vite"

if ($keepInfra) {
    Write-Host "`n== 已停前后端，依赖保留（下次 scripts\dev_up.ps1 直接秒起）=="
    exit 0
}

# ===== 2) PostgreSQL =====
if (-not (Test-Port 5433)) {
    Write-Host "[SKIP] PostgreSQL 未在运行" -ForegroundColor Yellow
} else {
    $pgCtl = Resolve-PgCtl
    if ($PgData -and (Test-Path $PgData)) {
        & (Resolve-PgCtl) -D $PgData stop -m fast 2>&1 | Out-Host
        Write-Host "[STOP] PostgreSQL（pg_ctl stop -m fast）" -ForegroundColor Green
    } elseif ($pgCtl) {
        $dataDir = Resolve-PgData $pgCtl
        & $pgCtl -D $dataDir stop -m fast 2>&1 | Out-Host
        Write-Host "[STOP] PostgreSQL（pg_ctl stop -m fast，数据目录 $dataDir）" -ForegroundColor Green
    } else {
        Write-Host "[WARN] 找不到 pg_ctl，请手动停止或填写脚本顶部 \$PgData" -ForegroundColor DarkYellow
    }
}

# ===== 3) Redis =====
if (-not (Test-Port 6379)) {
    Write-Host "[SKIP] Redis 未在运行" -ForegroundColor Yellow
} else {
    Write-Host "[STOP] Redis（redis-cli shutdown）"
    & $RedisCli shutdown nosave 2>&1 | Out-Host
    if (Test-Port 6379) { Write-Host "       redis-cli 不可用？请手动停止 Redis" -ForegroundColor DarkYellow }
}

# ===== 4) Ollama =====
Write-Host "[KEEP] Ollama 保持常驻（桌面应用自行管理；如需退出请在托盘退出）" -ForegroundColor DarkCyan

Write-Host "`n== 收工。下次一键拉起：powershell -File scripts\dev_up.ps1 ==" -ForegroundColor Cyan
