param(
  [switch]$TailLog
)

$ErrorActionPreference = 'Stop'

Write-Host "AI-Bridge: lanzando servicios en trabajos de PowerShell..." -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

try { chcp 65001 > $null } catch {}

# Cerrar instancias previas
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'server.py|claude-b-server.py|simple-watcher.ps1|watch-apply-bundle.ps1' } |
  ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }

# Arrancar como Jobs para ver estado en esta consola (sin nuevas ventanas)
Write-Host "- Iniciando Claude-A (8080)..." -ForegroundColor DarkCyan
$jobA = Start-Job -Name "aibridge-a" -ScriptBlock { Param($p)
  Set-Location $p; python server.py
} -ArgumentList $root

Write-Host "- Iniciando Claude-B (8081)..." -ForegroundColor DarkCyan
$jobB = Start-Job -Name "aibridge-b" -ScriptBlock { Param($p)
  Set-Location $p; python claude-b-server.py
} -ArgumentList $root

Write-Host "- Iniciando Watcher..." -ForegroundColor DarkCyan
$jobW = Start-Job -Name "aibridge-watcher" -ScriptBlock { Param($p)
  Set-Location $p; & powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File "$p\simple-watcher.ps1"
} -ArgumentList $root

Start-Sleep -Seconds 2

function Wait-Ready([string]$url,[string]$name){
  $max=30
  for($i=0;$i -lt $max;$i++){
    try { $r=Invoke-RestMethod -Uri $url -TimeoutSec 2; if($r){ Write-Host "[$name] OK" -ForegroundColor Green; return $true } }
    catch { Start-Sleep -Milliseconds 700 }
  }
  Write-Host "[$name] no responde" -ForegroundColor Yellow; return $false
}

$oka = Wait-Ready "http://localhost:8080/api/status" "Claude-A (8080)"
$okb = Wait-Ready "http://localhost:8081/api/status" "Claude-B (8081)"

Write-Host "UI: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Sugerencia: usa modo Colaborativo, desactiva autoaprobación si quieres aprobar manualmente, y observa Transcripción y Log." -ForegroundColor DarkGray
Write-Host "Decisiones rápidas: escribe 1 (yes), 2 (yes all), 3 (no) en [PAYLOAD] para aplicar sobre el último pendiente." -ForegroundColor DarkGray

if ($TailLog) {
  Write-Host "--- Log en vivo (Ctrl+C para salir) ---" -ForegroundColor Magenta
  Get-Content -Path "$root\messages\project.log" -Tail 100 -Wait
}

Write-Host "Jobs activos:" -ForegroundColor Cyan
Get-Job | Where-Object { $_.Name -like 'aibridge-*' } | Format-Table Id, Name, State -AutoSize

Write-Host "Para detener: Get-Job aibridge-* | Stop-Job -Force; Get-Job aibridge-* | Remove-Job" -ForegroundColor DarkGray

