# Initializes first message for Claude-A based on objective.txt
param()

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$objectiveFile = Join-Path $root "objective.txt"
$messagesDir = Join-Path $root "messages"
$targetFile = Join-Path $messagesDir "to_claude-a.txt"

if (-not (Test-Path $objectiveFile)) {
    Write-Host "objective.txt not found at $objectiveFile" -ForegroundColor Yellow
    exit 1
}

try {
    if (-not (Test-Path $messagesDir)) {
        New-Item -ItemType Directory -Path $messagesDir -Force | Out-Null
    }

    $objective = Get-Content -Path $objectiveFile -Raw
    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.ffffffZ')
    $message = @"
[TIMESTAMP]: $timestamp
[FROM]: system
[TO]: Claude-a
[ROLE]: system
[INTENT]: code
[LAST_SEEN]: none
[SUMMARY]:
- Initial objective
[PAYLOAD]:
$objective
"@
    Set-Content -Path $targetFile -Value $message
    Write-Host "Initial message written to $targetFile" -ForegroundColor Green
} catch {
    Write-Host "Error writing initial message: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
