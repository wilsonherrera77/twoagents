# File System Watcher for AI-Bridge
param(
    [string]$WatchPath = "C:\ai-bridge\messages",
    [string]$Action = "monitor"
)

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $WatchPath
$watcher.Filter = "*.txt"
$watcher.EnableRaisingEvents = $true

# Define what to do when a file is changed
$action = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    $timeStamp = $Event.TimeGenerated
    
    Write-Host "File $name was $changeType at $timeStamp" -ForegroundColor Yellow
    
    # Route to appropriate handler
    switch ($name) {
        "to_codex.txt" {
            Write-Host "Triggering Claude-A to Claude-B workflow" -ForegroundColor Cyan
            & "C:\ai-bridge\power-automate\scripts\trigger-claude-b.ps1" -MessageFile $path
        }
        "from_codex.txt" {
            Write-Host "Triggering Claude-B to Claude-A workflow" -ForegroundColor Cyan  
            & "C:\ai-bridge\power-automate\scripts\trigger-claude-a.ps1" -MessageFile $path
        }
    }
}

# Register event handlers
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action

Write-Host "File system watcher started. Monitoring: $WatchPath" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop..." -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    $watcher.Dispose()
}
