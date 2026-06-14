# Installe (ou met a jour) la tache planifiee Windows "TechwatchRefresh".
# Elle lance le pipeline techwatch tous les matins a 8h, meme sur batterie,
# avec rattrapage si la machine etait eteinte. A executer une seule fois :
#   powershell -ExecutionPolicy Bypass -File install_task.ps1
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$script = Join-Path $root "auto.py"
$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }  # fallback: console python

$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`"" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date "08:00")
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "TechwatchRefresh" -Action $action -Trigger $trigger `
  -Settings $settings -Description "techwatch : recuperation automatique des nouveautes RSS" -Force

Write-Host "Tache 'TechwatchRefresh' installee : tous les jours a 8h."
