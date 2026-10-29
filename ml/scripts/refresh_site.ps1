# Retrain on the current listings, then rewrite every number the site shows from them.
# Run after a collection: .\scripts\refresh_site.ps1  (from the ml folder)
$ml = Split-Path -Parent $PSScriptRoot
Set-Location $ml
$py = "$ml\.venv\Scripts\python.exe"
foreach ($module in "shotti_ml.run_current", "shotti_ml.export", "shotti_ml.run_duplicates", "shotti_ml.run_coldstart", "shotti_ml.export_site", "shotti_ml.export_check") {
    Write-Host "== $module"
    & $py -I -m $module
    if ($LASTEXITCODE -ne 0) { Write-Error "$module failed"; exit 1 }
}
Write-Host "Site data refreshed. Review with git diff web/src/lib/*.json"
