# PowerShell-script för FÖRBÄTTRAD schemaläggning  
# Optimerat för att säkerställa podcast-generering även om datorn sover

$TaskName = "ManniskaMaskinMiljo_WeeklyPodcast"
$Description = "Automatisk generering av Människa Maskin Miljö podcast varje onsdag kl 07:00 (med wake-up)"
$ScriptPath = "C:\Users\pontu\Documents\Autopodd\morgonradio\run_podcast.bat"

Write-Host "Skapar FÖRBÄTTRAD schemalagd uppgift för Människa Maskin Miljö..." -ForegroundColor Green

# Ta bort befintlig uppgift om den finns
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Tar bort gammal version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# FÖRBÄTTRAD trigger med wake-up
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At 7:00AM

# Action (samma som innan)
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`""

# FÖRBÄTTRADE settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

# Principal med högre behörigheter
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Password -RunLevel Highest

# Registrera förbättrad uppgift
Register-ScheduledTask -TaskName $TaskName -Description $Description -Trigger $Trigger -Action $Action -Settings $Settings -Principal $Principal

Write-Host "`n✅ FÖRBÄTTRAD schemalagd uppgift skapad!" -ForegroundColor Green
Write-Host "`n🔋 NYA FUNKTIONER:" -ForegroundColor Cyan
Write-Host "   ⏰ WakeToRun = Väcker datorn från viloläge" -ForegroundColor White
Write-Host "   🌐 RunOnlyIfNetworkAvailable = Väntar på internet" -ForegroundColor White  
Write-Host "   🔄 RestartCount 3 = Försöker igen om det misslyckas" -ForegroundColor White
Write-Host "   ⏱️ ExecutionTimeLimit 2h = Max körtid" -ForegroundColor White

Write-Host "`n💡 TIPS för bästa resultat:" -ForegroundColor Yellow
Write-Host "   1. Håll datorn inkopplad över natten" -ForegroundColor White
Write-Host "   2. Aktivera 'Allow wake timers' i Power Options" -ForegroundColor White
Write-Host "   3. Sätt datorns viloläge till 'Sleep' (inte 'Hibernate')" -ForegroundColor White

Write-Host "`n🔧 Aktivera wake timers med:" -ForegroundColor Yellow
Write-Host "   powercfg -setacvalueindex SCHEME_CURRENT SUB_SLEEP ALLOWWAKETIMERSFROMAC 001" -ForegroundColor Cyan
Write-Host "   powercfg -setdcvalueindex SCHEME_CURRENT SUB_SLEEP ALLOWWAKETIMERSFROMDC 001" -ForegroundColor Cyan
Write-Host "   powercfg -setactive SCHEME_CURRENT" -ForegroundColor Cyan
