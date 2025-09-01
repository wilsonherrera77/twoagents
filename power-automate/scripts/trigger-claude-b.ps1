# Trigger Claude-B Response
param(
    [string]$MessageFile
)

Write-Host "Processing message for Claude-B: $MessageFile" -ForegroundColor Cyan

try {
    $messageContent = Get-Content -Path $MessageFile -Raw
    
    # Parse message components
    $timestamp = [regex]::Match($messageContent, '\[TIMESTAMP\]: (.+)').Groups[1].Value
    $from = [regex]::Match($messageContent, '\[FROM\]: (.+)').Groups[1].Value  
    $intent = [regex]::Match($messageContent, '\[INTENT\]: (.+)').Groups[1].Value
    $payload = [regex]::Match($messageContent, '\[PAYLOAD\]:\s*(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline).Groups[1].Value
    
    # Create request body
    $body = @{
        timestamp = $timestamp
        from = $from
        intent = $intent
        content = $payload.Trim()
    } | ConvertTo-Json
    
    # Send to Claude-B
    $response = Invoke-RestMethod -Uri "http://localhost:8081/api/receive_message" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "Message forwarded to Claude-B successfully" -ForegroundColor Green
    
    # Log the transaction
    $logEntry = "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Claude-A -> Claude-B: $intent"
    Add-Content -Path "C:\ai-bridge\power-automate\logs\communication.log" -Value $logEntry
    
} catch {
    Write-Host "Error processing message: $($_.Exception.Message)" -ForegroundColor Red
}
