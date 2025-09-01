param([string]$From="Claude",[string]$LastSeen="")
$iso = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
# inyecta encabezado si falta
$text = Get-Content C:\ai-bridge\to_codex.txt -Raw
if ($text -notmatch "^\[TIMESTAMP\]:") {
  $hdr = "[TIMESTAMP]: $iso`n[FROM]: $From`n[TO]: Codex`n[ROLE]: Mentor`n[INTENT]: plan`n[LAST_SEEN]: $LastSeen`n"
  $text = $hdr + "`n" + $text
}
Set-Clipboard -Value $text
Add-Content C:\ai-bridge\log_codex.md "`n`n## >> $(Get-Date -Format u) enviado a Codex`n$text"
Write-Host "[Listo] Mensaje para Codex copiado al portapapeles."