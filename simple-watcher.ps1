# Simple File Watcher for AI-Bridge
Write-Host "Starting Simple File Watcher for AI-Bridge..." -ForegroundColor Green
Write-Host "[POLICY] Agents are authorized to use local PC resources without restriction to reach the objective (no intermediate user prompts)." -ForegroundColor Yellow

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchPath = Join-Path $root "messages"
$logPath = Join-Path $watchPath "project.log"

function Write-ProjectLog($level, $msg){
  try{
    if (-not (Test-Path $watchPath)) { New-Item -ItemType Directory -Path $watchPath -Force | Out-Null }
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Add-Content -Path $logPath -Value "$ts [WATCHER][$level] $msg"
  } catch {}
}
$lastCheck = @{}

Write-Host "Monitoring directory: $watchPath" -ForegroundColor Cyan
Write-ProjectLog 'start' "watching $watchPath"
Write-Host "Watching for: to_claude-b.txt and from_claude-a.txt" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow
Write-Host ""

while ($true) {
    try {
        # Check to_claude-b.txt (Claude-A to Claude-B)
        $toClaudeBFile = Join-Path $watchPath "to_claude-b.txt"
        if (Test-Path $toClaudeBFile) {
            $currentTime = (Get-Item $toClaudeBFile).LastWriteTime
            
            if (-not $lastCheck.ContainsKey("to_claude-b") -or $lastCheck["to_claude-b"] -ne $currentTime) {
                $lastCheck["to_claude-b"] = $currentTime
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] to_claude-b.txt updated - Triggering Claude-B" -ForegroundColor Cyan
                
                # Trigger Claude-B
                try {
                    $messageContent = Get-Content -Path $toClaudeBFile -Raw
                    
                    # Extract payload section (multiline)
                    $m = [regex]::Match($messageContent, '(?s)\[PAYLOAD\]:\s*(.*)$')
                    if ($m.Success) {
                        $payload = $m.Groups[1].Value.Trim()
                        
                        # Create request body for Claude-B
                        $body = @{
                            content = $payload
                            intent = "plan"
                        } | ConvertTo-Json
                        
                        # Send to Claude-B
                        $response = Invoke-RestMethod -Uri "http://localhost:8081/api/send_message" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
                        Write-Host "  -> Message forwarded to Claude-B successfully" -ForegroundColor Green
                        Write-ProjectLog 'info' 'forwarded file payload to claude-b'
                    }
                } catch {
                    Write-Host "  -> Error forwarding to Claude-B: $($_.Exception.Message)" -ForegroundColor Red
                    Write-ProjectLog 'warn' ("forward to claude-b failed: " + $_.Exception.Message)
                }
            }
        }
        
        # Check from_claude-b.txt (Claude-B to Claude-A)  
        $fromClaudeBFile = Join-Path $watchPath "from_claude-b.txt"
        if (Test-Path $fromClaudeBFile) {
            $currentTime = (Get-Item $fromClaudeBFile).LastWriteTime
            
            if (-not $lastCheck.ContainsKey("from_claude-b") -or $lastCheck["from_claude-b"] -ne $currentTime) {
                $lastCheck["from_claude-b"] = $currentTime
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] from_claude-b.txt updated - Triggering Claude-A" -ForegroundColor Magenta
                
                # Trigger Claude-A response
                try {
                    $responseContent = Get-Content -Path $fromClaudeBFile -Raw
                    
                    # Extract payload section (multiline)
                    $m = [regex]::Match($responseContent, '(?s)\[PAYLOAD\]:\s*(.*)$')
                    if ($m.Success) {
                        $payload = $m.Groups[1].Value.Trim()
                        
                        # Create request body for Claude-A
                        $body = @{
                            content = $payload
                            intent = "code"
                        } | ConvertTo-Json
                        
                        # Send to Claude-A
                        $response = Invoke-RestMethod -Uri "http://localhost:8080/api/send_message" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
                        Write-Host "  -> Response forwarded to Claude-A successfully" -ForegroundColor Green
                        Write-ProjectLog 'info' 'forwarded file payload to claude-a'
                    }
                } catch {
                    Write-Host "  -> Error forwarding to Claude-A: $($_.Exception.Message)" -ForegroundColor Red
                    Write-ProjectLog 'warn' ("forward to claude-a failed: " + $_.Exception.Message)
                }
            }
        }
        
        # Wait 2 seconds before next check
        Start-Sleep -Seconds 2
        
    } catch {
        Write-Host "Watcher error: $($_.Exception.Message)" -ForegroundColor Red
        Write-ProjectLog 'error' ("watcher error: " + $_.Exception.Message)
        Start-Sleep -Seconds 5
    }
}
