# Synco installer (Windows)
# - Creates a Python venv in .\venv
# - Creates start.bat and stop.bat wrappers

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Output "[synco] Project directory: $ProjectDir"

# Try python; user can adjust to 'py' if needed
$pythonCmd = "python"
$pythonExists = $false
try {
    & $pythonCmd --version > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pythonExists = $true
    }
} catch {
    $pythonExists = $false
}

if (-not $pythonExists) {
    Write-Output "[synco] 'python' not found. Install Python 3 and ensure it's in PATH."
    exit 1
}

Write-Output "[synco] Creating virtual environment..."
& $pythonCmd -m venv "$ProjectDir\venv"

Write-Output "[synco] Upgrading pip inside venv..."
& "$ProjectDir\venv\Scripts\python.exe" -m pip install --upgrade pip > $null

Write-Output "[synco] Creating start.bat..."
"@echo off" > "$ProjectDir\start.bat"
"cd /d %~dp0" >> "$ProjectDir\start.bat"
"venv\Scripts\python.exe main.py" >> "$ProjectDir\start.bat"

Write-Output "[synco] Creating stop.bat..."
"@echo off" > "$ProjectDir\stop.bat"
"cd /d %~dp0" >> "$ProjectDir\stop.bat"
"venv\Scripts\python.exe main.py --stop" >> "$ProjectDir\stop.bat"

Write-Output ""
Write-Output "[synco] Install complete."
Write-Output "Next steps:"
Write-Output "  1. Install rclone for Windows and add it to PATH."
Write-Output "  2. Create and edit synco.json in this folder."
Write-Output "  3. Double-click start.bat to start syncing."
Write-Output "  4. Double-click stop.bat to stop."
