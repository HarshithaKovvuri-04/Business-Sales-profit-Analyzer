# Helper: kill uvicorn/python processes started for this project
# Usage: run from repository root: `powershell -ExecutionPolicy Bypass -File .\backend\scripts\kill_uvicorn.ps1`
# This searches for processes whose command line contains 'uvicorn' or 'app.main:app' and stops them.

$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'uvicorn' -or $_.CommandLine -match 'app.main:app' -or $_.CommandLine -match 'start_uvicorn_with_env.py') }
if (-not $procs) {
    Write-Output "No uvicorn/python processes found matching project criteria."
    exit 0
}

foreach ($p in $procs) {
    try {
        Write-Output "Stopping PID $($p.ProcessId): $($p.CommandLine)"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
    } catch {
        Write-Warning "Failed to stop PID $($p.ProcessId): $_"
    }
}
Write-Output "Done."
