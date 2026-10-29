# Weekly GarirBazar snapshot, meant to run from Windows Task Scheduler (task name "ShottiWeeklyCollect").
# A different page sample each week (seed = day of the year) so snapshots overlap but don't repeat.
$ml = Split-Path -Parent $PSScriptRoot
Set-Location $ml
$seed = (Get-Date).DayOfYear
& "$ml\.venv\Scripts\python.exe" -I -m shotti_ml.collect.run --pages 100 --seed $seed *>> "$ml\data\raw\weekly.log"
