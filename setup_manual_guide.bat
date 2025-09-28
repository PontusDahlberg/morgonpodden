@echo off
echo.
echo ===============================================
echo SMART TASK SETUP (MANUELL)
echo ===============================================
echo.
echo Denna guide hjälper dig sätta upp automatisk
echo podcast-övervakning manuellt via Task Scheduler.
echo.
echo 1. Öppna Task Scheduler (schtasks eller GUI)
echo 2. Högerklicka "Task Scheduler Library"
echo 3. Välj "Create Basic Task"
echo.
echo INSTÄLLNINGAR:
echo --------------
echo Namn: SmartPodcastMonitor
echo Beskrivning: Smart podcast-övervakning
echo.
echo TRIGGER: 
echo - Välj "Daily"
echo - Tid: 18:00:00
echo - Återkommer var: 1 dag
echo.
echo ACTION:
echo - Start a program
echo - Program: %~dp0run_smart_monitor.bat
echo - Start in: %~dp0
echo.
echo AVANCERAT (valfritt):
echo - Lägg till extra trigger för "At startup" 
echo - Fördröjning: 2 minuter
echo.
echo ===============================================
echo ALTERNATIV: Lägg till i Windows Startup
echo ===============================================
echo.
echo 1. Tryck Win+R, skriv: shell:startup
echo 2. Kopiera run_smart_monitor.bat till mappen
echo 3. Redigera för att köra endast en gång
echo.
echo Script-sökväg: %~dp0run_smart_monitor.bat
echo Working directory: %~dp0
echo.
pause
