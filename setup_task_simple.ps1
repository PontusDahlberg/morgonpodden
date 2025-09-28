# Windows Task Scheduler Setup för Podcast Nedladdning
Write-Host "Skapar Windows Task för automatisk podcast-nedladdning..." -ForegroundColor Green

$TaskName = "AutoPodcastDownload"
$TaskDescription = "Hämtar automatiskt nya podcast-avsnitt"
$ScriptPath = "C:\Users\pontu\Documents\Autopodd\morgonradio\run_auto_download.bat"
$WorkingDirectory = "C:\Users\pontu\Documents\Autopodd\morgonradio"

# Kontrollera att script-filen finns
if (-not (Test-Path $ScriptPath)) {
    Write-Host "Fel: Kan inte hitta $ScriptPath" -ForegroundColor Red
    exit 1
}

# Ta bort befintlig task om den finns
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Tar bort befintlig task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Skapa trigger - varje dag kl 19:00
$Trigger = New-ScheduledTaskTrigger -Daily -At "19:00"

# Skapa action
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# Skapa settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Registrera task
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description $TaskDescription
    
    Write-Host "Task skapad framgångsrikt!" -ForegroundColor Green
    Write-Host "Schemalagd att köras varje dag kl 19:00" -ForegroundColor Cyan
    
} catch {
    Write-Host "Fel vid skapande av task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Visa information
Get-ScheduledTask -TaskName $TaskName | Format-Table TaskName, State
