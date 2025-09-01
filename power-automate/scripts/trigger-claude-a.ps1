# Trigger Claude-A Response  
param(
    [string]$MessageFile
)

Write-Host "Processing response for Claude-A: $MessageFile" -ForegroundColor Cyan

try {
    $responseContent = Get-Content -Path $MessageFile -Raw
    
    # Parse response components
    $timestamp = [regex]::Match($responseContent, '\[TIMESTAMP\]: (.+)').Groups[1].Value
    $from = [regex]::Match($responseContent, '\[FROM\]: (.+)').Groups[1].Value
    $intent = [regex]::Match($responseContent, '\[INTENT\]: (.+)').Groups[1].Value  
    $payload = [regex]::Match($responseContent, '\[PAYLOAD\]:\s*(.*)', [System.Text.RegularExpressions.RegexOptions]::Singleline).Groups[1].Value
    
    # Create request body
    $body = @{
        timestamp = $timestamp
        from = $from
        intent = $intent
        content = $payload.Trim()
    } | ConvertTo-Json
    
    # Send to Claude-A
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/receive_message" -Method POST -Body $body -ContentType "application/json"
    
    Write-Host "Response forwarded to Claude-A successfully" -ForegroundColor Green
    
    # Log the transaction
    $logEntry = "[$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')] Claude-B -> Claude-A: $intent"
    Add-Content -Path "C:\ai-bridge\power-automate\logs\communication.log" -Value $logEntry
    
} catch {
    Write-Host "Error processing response: $($_.Exception.Message)" -ForegroundColor Red
}
