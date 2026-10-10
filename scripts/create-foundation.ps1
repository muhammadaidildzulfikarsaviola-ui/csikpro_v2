$ErrorActionPreference = "Stop"

$root = "D:\Code\Sikpro-v2-with-c"

if (!(Test-Path "$root\engine\python\sikpro\engine")) {
    throw "Folder engine Python tidak ditemukan. Proses dihentikan."
}

if (!(Test-Path "$root\.venv\Scripts\python.exe")) {
    throw "Python virtual environment tidak ditemukan. Proses dihentikan."
}

Write-Host "Project root : $root"
Write-Host "Python       : $root\.venv\Scripts\python.exe"
Write-Host ""
Write-Host "Environment verified. Foundation generator can be created."
