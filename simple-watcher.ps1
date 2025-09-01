# Simple File Watcher for AI-Bridge
Write-Host "Starting Simple File Watcher for AI-Bridge..." -ForegroundColor Green
Write-Host "[POLICY] Agents are authorized to use local PC resources without restriction to reach the objective (no intermediate user prompts)." -ForegroundColor Yellow

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchPath = Join-Path $root "messages"
$logPath = Join-Path $watchPath "project.log"
$workspacePath = Join-Path $root "workspace"

function Write-ProjectLog($level, $msg){
  try{
    if (-not (Test-Path $watchPath)) { New-Item -ItemType Directory -Path $watchPath -Force | Out-Null }
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Add-Content -Path $logPath -Value "$ts [WATCHER][$level] $msg"
  } catch {}
}
$lastCheck = @{}

function Test-WorkspaceNotEmpty {
    $item = Get-ChildItem -Path $workspacePath -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    return $null -ne $item
}

if (Test-WorkspaceNotEmpty) {
    Write-Host "workspace contains skeleton files." -ForegroundColor Green
} else {
    Write-Host "workspace is empty; waiting for at least one skeleton file..." -ForegroundColor Yellow
}

Write-Host "Monitoring directory: $watchPath" -ForegroundColor Cyan
Write-ProjectLog 'start' "watching $watchPath"
Write-Host "Watching for: to_claude-b.txt, from_claude-b.txt, and to_claude-a.txt" -ForegroundColor Cyan

# Send initial objective to Claude-A if present
$toClaudeAInit = Join-Path $watchPath "to_claude-a.txt"
if (Test-Path $toClaudeAInit) {
    try {
        $initContent = Get-Content -Path $toClaudeAInit -Raw
        $m = [regex]::Match($initContent, '(?s)\[PAYLOAD\]:\s*(.*)$')
        if ($m.Success) {
            $payload = $m.Groups[1].Value.Trim()
            $body = @{ content = $payload; intent = "code" } | ConvertTo-Json
            $response = Invoke-RestMethod -Uri "http://localhost:8080/api/send_message" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
            Write-Host "Initial to_claude-a.txt sent to Claude-A" -ForegroundColor Green
            Write-ProjectLog 'info' 'initial to_claude-a forwarded to claude-a'
        }
        $lastCheck['to_claude-a'] = (Get-Item $toClaudeAInit).LastWriteTime
    } catch {
        Write-Host "Error forwarding initial to_claude-a.txt: $($_.Exception.Message)" -ForegroundColor Red
        Write-ProjectLog 'warn' ("initial to_claude-a forward failed: " + $_.Exception.Message)
    }
}

Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow
Write-Host ""

$emptyIterations = 0

while ($true) {
    if (-not (Test-WorkspaceNotEmpty)) {
        $emptyIterations++
        if ($emptyIterations -ge 2) {
            Write-Host "workspace still empty after two checks. Stopping watcher." -ForegroundColor Red
            Write-ProjectLog 'warn' 'workspace empty after two iterations - stopping'
            break
        }
    } else {
        $emptyIterations = 0
    }

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

        # Check to_claude-a.txt (messages to Claude-A)
        $toClaudeAFile = Join-Path $watchPath "to_claude-a.txt"
        if (Test-Path $toClaudeAFile) {
            $currentTime = (Get-Item $toClaudeAFile).LastWriteTime

            if (-not $lastCheck.ContainsKey("to_claude-a") -or $lastCheck["to_claude-a"] -ne $currentTime) {
                $lastCheck["to_claude-a"] = $currentTime
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] to_claude-a.txt updated - Triggering Claude-A" -ForegroundColor Green

                try {
                    $messageContent = Get-Content -Path $toClaudeAFile -Raw

                    # Extract payload section (multiline)
                    $m = [regex]::Match($messageContent, '(?s)\[PAYLOAD\]:\s*(.*)$')
                    if ($m.Success) {
                        $payload = $m.Groups[1].Value.Trim()

                        # Create request body for Claude-A
                        $body = @{
                            content = $payload
                            intent = "code"
                        } | ConvertTo-Json

                        # Send to Claude-A
                        $response = Invoke-RestMethod -Uri "http://localhost:8080/api/send_message" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
                        Write-Host "  -> Message forwarded to Claude-A successfully" -ForegroundColor Green
                        Write-ProjectLog 'info' 'forwarded file payload to claude-a (to_claude-a)'
                    }
                } catch {
                    Write-Host "  -> Error forwarding to Claude-A: $($_.Exception.Message)" -ForegroundColor Red
                    Write-ProjectLog 'warn' ("forward to claude-a (to_claude-a) failed: " + $_.Exception.Message)
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
