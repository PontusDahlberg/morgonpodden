# Windows Task Scheduler Setup för Podcast Nedladdning
# Kör som Administrator: PowerShell -ExecutionPolicy Bypass -File "setup_task_scheduler.ps1"

Write-Host "🔧 Skapar Windows Task för automatisk podcast-nedladdning..." -ForegroundColor Green

# Definiera task-parametrar
$TaskName = "AutoPodcastDownload"
$TaskDescription = "Hämtar automatiskt nya podcast-avsnitt från Cloudflare och GitHub"
$ScriptPath = "C:\Users\pontu\Documents\Autopodd\morgonradio\run_auto_download.bat"
$WorkingDirectory = "C:\Users\pontu\Documents\Autopodd\morgonradio"

# Kontrollera att script-filen finns
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Fel: Kan inte hitta $ScriptPath" -ForegroundColor Red
    exit 1
}

# Ta bort befintlig task om den finns
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "🗑️ Tar bort befintlig task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Skapa trigger - varje dag kl 19:00
$Trigger = New-ScheduledTaskTrigger -Daily -At "19:00"

# Skapa action - kör batch-scriptet
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# Skapa settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Skapa principal - kör som current user
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Registrera task
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Principal $Principal -Description $TaskDescription
    
    Write-Host "✅ Task skapad framgångsrikt!" -ForegroundColor Green
    Write-Host "📅 Schemalagd att köras varje dag kl 19:00" -ForegroundColor Cyan
    Write-Host "🔍 Kontrollera: Öppna Task Scheduler och leta efter '$TaskName'" -ForegroundColor Cyan
    
    # Testa att köra task manuellt
    Write-Host "🧪 Testar att köra task manuellt..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName
    
    Write-Host "✅ Setup klar! Task kommer att köras automatiskt varje dag." -ForegroundColor Green
    
} catch {
    Write-Host "❌ Fel vid skapande av task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Visa information om skapad task
Write-Host "`n📋 Task-information:" -ForegroundColor Cyan
Get-ScheduledTask -TaskName $TaskName | Format-Table TaskName, State, @{Name="NextRunTime";Expression={(Get-ScheduledTask $_.TaskName | Get-ScheduledTaskInfo).NextRunTime}}

Write-Host "`n🎯 För att hantera task manuellt:" -ForegroundColor Yellow
Write-Host "   - Starta: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   - Stoppa: Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "   - Ta bort: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
