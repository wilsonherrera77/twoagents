param(
  [switch]$NoWatcher
)

Write-Host "AI-Bridge: arrancando servidores y probando E2E..." -ForegroundColor Cyan
Write-Host "[POLITICA] Los agentes estan AUTORIZADOS para usar los recursos locales de la PC sin restricciones para alcanzar el objetivo (sin solicitar aprobaciones intermedias)." -ForegroundColor Yellow

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Arrancar servidores en nuevas ventanas
Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/k","title AI-Bridge Frontend (8080) & python server.py"
Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/k","title Claude-B Server (8081) & python claude-b-server.py"

if (-not $NoWatcher) {
  Start-Process -WindowStyle Normal -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy","Bypass","-NoLogo","-NoProfile","-File","$root\simple-watcher.ps1"
}

Start-Sleep -Seconds 3

function Wait-Ready($url,$name){
  $max=15; for($i=0;$i -lt $max;$i++){ try{ $r=Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 2; if($r){ Write-Host "[$name] OK" -ForegroundColor Green; return $true } } catch { Start-Sleep -Milliseconds 400 } }; Write-Host "[$name] no responde" -ForegroundColor Yellow; return $false }

$okA = Wait-Ready "http://localhost:8080/api/status" "Claude-A (8080)"
$okB = Wait-Ready "http://localhost:8081/api/status" "Claude-B (8081)"

# Pruebas mínimas E2E
try {
  $plan = [pscustomobject]@{ id=1; timestamp=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); role='mentor'; intent='plan'; content=[pscustomobject]@{ steps=@(1,2,3); note='auto' } }
  $planJson = $plan | ConvertTo-Json -Depth 6
  $r1 = Invoke-RestMethod -Method Post -Uri "http://localhost:8081/api/receive_message" -Body $planJson -ContentType 'application/json' -TimeoutSec 5
  Write-Host "POST /api/receive_message (B) =>" ($r1 | ConvertTo-Json -Depth 4) -ForegroundColor Green
} catch { Write-Host "Fallo receive_message(B): $($_.Exception.Message)" -ForegroundColor Red }

try {
  $msg = [pscustomobject]@{ content='Ping desde script'; intent='code' }
  $msgJson = $msg | ConvertTo-Json -Depth 3
  $r2 = Invoke-RestMethod -Method Post -Uri "http://localhost:8081/api/send_message" -Body $msgJson -ContentType 'application/json' -TimeoutSec 5
  Write-Host "POST /api/send_message (B) =>" ($r2 | ConvertTo-Json -Depth 4) -ForegroundColor Green
} catch { Write-Host "Fallo send_message(B): $($_.Exception.Message)" -ForegroundColor Red }

try {
  $msgs = Invoke-RestMethod -Method Get -Uri "http://localhost:8081/api/messages" -TimeoutSec 5
  Write-Host "GET /api/messages (B) =>" ($msgs | ConvertTo-Json -Depth 6) -ForegroundColor Green
} catch { Write-Host "Fallo messages(B): $($_.Exception.Message)" -ForegroundColor Red }

Write-Host "Listo. Ventanas quedarán abiertas. Puedes cerrar este script." -ForegroundColor Cyan
