param([string]$From="Codex",[string]$LastSeen="")
$iso = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$text = Get-Content C:\ai-bridge\to_claude.txt -Raw
if ($text -notmatch "^\[TIMESTAMP\]:") {
  $hdr = "[TIMESTAMP]: $iso`n[FROM]: $From`n[TO]: Claude`n[ROLE]: Implementador`n[INTENT]: code`n[LAST_SEEN]: $LastSeen`n"
  $text = $hdr + "`n" + $text
}
Set-Clipboard -Value $text
Add-Content C:\ai-bridge\log_claude.md "`n`n## >> $(Get-Date -Format u) enviado a Claude`n$text"
Write-Host "[Listo] Mensaje para Claude copiado al portapapeles."