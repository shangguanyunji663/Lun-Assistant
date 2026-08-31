# Convert GBK-encoded text files to UTF-8 (ASCII-safe script)
$root = 'D:\PythonProject\Lun-Assistant'
$enc = [Text.Encoding]::GetEncoding('GBK')
$utf8 = New-Object Text.UTF8Encoding($false)
$files = Get-ChildItem $root -Recurse -File -Include *.py,*.yaml,*.yml,.env,.env.example,.gitignore,*.md,*.json | Where-Object { $_.FullName -notmatch '\\envs\\' -and $_.FullName -notmatch 'node_modules' }
foreach ($f in $files) {
    $bytes = [IO.File]::ReadAllBytes($f.FullName)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { continue }
    $isUtf8 = $false
    try { $strict = New-Object Text.UTF8Encoding($false, $true); $null = $strict.GetString($bytes); $isUtf8 = $true } catch { $isUtf8 = $false }
    if ($isUtf8) { continue }
    $text = $enc.GetString($bytes)
    [IO.File]::WriteAllText($f.FullName, $text, $utf8)
    Write-Output "converted: $($f.FullName.Substring($root.Length + 1))"
}
Write-Output "done"
