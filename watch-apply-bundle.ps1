param(
  [string]$SourceFile = $(Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'messages\from_claude-b.txt'),
  [int]$IntervalSec = 2
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$messagesDir = Join-Path $root 'messages'
$logPath = Join-Path $messagesDir 'project.log'

function Write-ProjectLog($level, $msg){
  try{
    if (-not (Test-Path $messagesDir)) { New-Item -ItemType Directory -Path $messagesDir -Force | Out-Null }
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Add-Content -Path $logPath -Value "$ts [BUNDLE-WATCH][$level] $msg"
  } catch {}
}

Write-Host "[BUNDLE] Watching for bundle JSON in: $SourceFile" -ForegroundColor Cyan
Write-ProjectLog 'start' "bundle watcher started: $SourceFile"

$lastTime = $null
while ($true) {
  try {
    if (Test-Path $SourceFile) {
      $mt = (Get-Item $SourceFile).LastWriteTime
      if ($lastTime -eq $null -or $mt -gt $lastTime) {
        $lastTime = $mt
        $content = Get-Content -Path $SourceFile -Raw
        # Extract payload block after [PAYLOAD]:
        $m = [regex]::Match($content, '(?s)\[PAYLOAD\]:\s*(.*)$')
        if ($m.Success) {
          $payload = $m.Groups[1].Value
          # Try to locate a JSON object inside payload
          $jsonMatch = [regex]::Match($payload, '(?s)\{.*\}')
          if ($jsonMatch.Success) {
            try {
              $obj = $jsonMatch.Value | ConvertFrom-Json -ErrorAction Stop
              if ($obj.files -and $obj.files.Count -gt 0) {
                $base = if ([string]::IsNullOrWhiteSpace($obj.base_dir)) { 'prueba3' } else { [string]$obj.base_dir }
                $applied = 0
                foreach ($f in $obj.files) {
                  try {
                    $rel = [string]$f.path
                    $data = [pscustomobject]@{ path = ("$base/" + $rel); content = [string]$f.content }
                    $body = $data | ConvertTo-Json -Depth 8
                    Invoke-RestMethod -Uri 'http://localhost:8080/api/create_file' -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 10 | Out-Null
                    $applied++
                  } catch {
                    Write-ProjectLog 'warn' ("bundle file apply failed: " + $_.Exception.Message)
                  }
                }
                Write-Host "[BUNDLE] Applied $applied files to workspace/$base" -ForegroundColor Green
                Write-ProjectLog 'info' "bundle applied files=$applied base=$base"
              }
            } catch {
              Write-ProjectLog 'warn' ("bundle JSON parse failed: " + $_.Exception.Message)
            }
          } else {
            Write-ProjectLog 'debug' 'payload has no JSON object'
          }
        }
      }
    }
  } catch {
    Write-ProjectLog 'error' ("bundle watcher loop error: " + $_.Exception.Message)
  }
  Start-Sleep -Seconds $IntervalSec
}

