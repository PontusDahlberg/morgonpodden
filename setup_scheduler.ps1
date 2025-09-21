# PowerShell-script för att skapa schemalagd uppgift
# Kör detta script som administratör

$TaskName = "ManniskaMaskinMiljo_WeeklyPodcast"
$Description = "Automatisk generering av Människa Maskin Miljö podcast varje onsdag kl 07:00"
$ScriptPath = "C:\Users\pontu\Documents\Autopodd\morgonradio\run_podcast.bat"

Write-Host "Skapar schemalagd uppgift för Människa Maskin Miljö..." -ForegroundColor Green

# Kontrollera om uppgiften redan finns
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Uppgiften finns redan. Tar bort gammal version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Skapa ny trigger (varje onsdag kl 07:00)
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At 7:00AM

# Skapa action (kör batch-script)
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ScriptPath`""

# Skapa settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Skapa principal (kör som current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Registrera uppgiften
Register-ScheduledTask -TaskName $TaskName -Description $Description -Trigger $Trigger -Action $Action -Settings $Settings -Principal $Principal

Write-Host "`n✅ Schemalagd uppgift skapad!" -ForegroundColor Green
Write-Host "Uppgiftsnamn: $TaskName" -ForegroundColor Cyan
Write-Host "Schema: Varje onsdag kl 07:00" -ForegroundColor Cyan
Write-Host "Script: $ScriptPath" -ForegroundColor Cyan

Write-Host "`n🔍 Du kan kontrollera uppgiften i Task Scheduler:" -ForegroundColor Yellow
Write-Host "   1. Tryck Win+R, skriv 'taskschd.msc' och tryck Enter" -ForegroundColor White
Write-Host "   2. Hitta '$TaskName' i listan" -ForegroundColor White
Write-Host "   3. Högerklicka och välj 'Run' för att testa" -ForegroundColor White

Write-Host "`n📝 Logfiler sparas i:" -ForegroundColor Yellow
Write-Host "   $((Split-Path $ScriptPath -Parent))\podcast_log.txt" -ForegroundColor White
