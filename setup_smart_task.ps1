# Smart Task Scheduler Setup
Write-Host "Skapar smart podcast monitoring..." -ForegroundColor Green

# Ta bort gamla task
$OldTask = Get-ScheduledTask -TaskName "AutoPodcastDownload" -ErrorAction SilentlyContinue
if ($OldTask) {
    Write-Host "Tar bort gamla task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "AutoPodcastDownload" -Confirm:$false
}

# Nya task-parametrar
$TaskName = "SmartPodcastMonitor"
$TaskDescription = "Smart podcast-övervakning - daglig kl 18:00 + onsdag extra"
$ScriptPath = "C:\Users\pontu\Documents\Autopodd\morgonradio\run_smart_monitor.bat"
$WorkingDirectory = "C:\Users\pontu\Documents\Autopodd\morgonradio"

# Kontrollera script
if (-not (Test-Path $ScriptPath)) {
    Write-Host "Fel: Kan inte hitta $ScriptPath" -ForegroundColor Red
    exit 1
}

# Skapa triggers
$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "18:00"

# Trigger vid datorstart (vänta 2 minuter)
$StartupTrigger = New-ScheduledTaskTrigger -AtStartup
$StartupTrigger.Delay = "PT2M"

# Skapa action
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# Skapa settings - enklare version
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Registrera task
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger @($DailyTrigger, $StartupTrigger) -Action $Action -Settings $Settings -Description $TaskDescription -User $env:USERNAME
    
    Write-Host "Smart task skapad!" -ForegroundColor Green
    Write-Host "- Daglig körning: 18:00" -ForegroundColor Cyan  
    Write-Host "- Startup-trigger: 2 min efter boot" -ForegroundColor Cyan
    Write-Host "- Auto-restart vid fel" -ForegroundColor Cyan
    
} catch {
    Write-Host "Fel: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Visa status
Get-ScheduledTask -TaskName $TaskName | Format-Table TaskName, State

Write-Host "Setup klar! Smart monitoring aktivt." -ForegroundColor Green
