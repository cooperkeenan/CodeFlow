$VenvDir = ".venv"
$PidFile = ".pids"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$UvicornBin = "$RootDir\$VenvDir\Scripts\uvicorn.exe"

function Start-Service {
    param (
        [string]$Name,
        [string]$Dir,
        [int]$Port
    )
    $env:PYTHONPATH = $RootDir
    $process = Start-Process `
        -FilePath $UvicornBin `
        -ArgumentList "main:app --app-dir $RootDir\$Dir --host 0.0.0.0 --port $Port --reload" `
        -PassThru -NoNewWindow
    Add-Content -Path "$RootDir\$PidFile" -Value $process.Id
    Write-Host "  OK $Name on port $Port (pid $($process.Id))"
}

function Kill-Ports {
    $ports = 8000, 8002, 8003, 8004, 5173, 5174, 5175, 5176, 5177
    foreach ($port in $ports) {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "  Cleared port $port"
        }
    }
}

function Get-EnvValue {
    param ([string]$Key)
    $line = Get-Content "$RootDir\.env" -ErrorAction SilentlyContinue |
        Where-Object { $_ -match "^$Key=" } |
        Select-Object -First 1
    if ($line) {
        return ($line -split "=", 2)[1].Trim()
    }
    return $null
}

New-Item -Path "$RootDir\$PidFile" -ItemType File -Force | Out-Null

Write-Host ""
Write-Host "==============================="
Write-Host "   CodeFlow Dev Runner"
Write-Host "==============================="
Write-Host ""

if (-not (Test-Path $UvicornBin)) {
    Write-Host "ERROR: uvicorn not found at $UvicornBin"
    exit 1
}

Write-Host "Clearing ports..."
Kill-Ports
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "Starting services..."
Start-Service -Name "API Gateway"    -Dir "api"                   -Port 8000
Start-Service -Name "Profiler Agent" -Dir "agents\profiler_agent" -Port 8002
Start-Service -Name "Tracer Agent"   -Dir "agents\tracer_agent"   -Port 8003
Start-Service -Name "Render Agent"   -Dir "agents\render_agent"   -Port 8004

$localRepo = Get-EnvValue -Key "LOCAL_REPO"

if ($localRepo -eq "true") {
    Write-Host ""
    Write-Host "LOCAL_REPO mode - skipping frontend"
    Write-Host "Waiting for services to start..."
    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "Triggering local analysis..."
    try {
        $response = Invoke-RestMethod `
            -Uri "http://localhost:8000/analyse/local" `
            -Method POST `
            -ContentType "application/json"

        Write-Host ""
        Write-Host "Analysis complete:"
        $response | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "ERROR: Analysis failed - $($_.Exception.Message)"
        Write-Host "Check service logs above for details"
    }
} else {
    Write-Host ""
    Write-Host "Starting frontend..."
    $frontend = Start-Process -FilePath "npm.cmd" `
        -ArgumentList "run dev" `
        -WorkingDirectory "$RootDir\frontend" `
        -PassThru -NoNewWindow
    Add-Content -Path "$RootDir\$PidFile" -Value $frontend.Id
    Write-Host "  OK Frontend on port 5173 (pid $($frontend.Id))"

    Write-Host ""
    Write-Host "All services running. PIDs saved to .pids"
}
