@echo off
REM Script för att kontrollera status på Människa Maskin Miljö automatisering

echo ================================================
echo   MÄNNISKA MASKIN MILJÖ - SYSTEMSTATUS
echo ================================================
echo.

echo 📅 SCHEMALAGD UPPGIFT:
schtasks /query /tn "ManniskaMaskinMiljo_WeeklyPodcast" /fo LIST | findstr /C:"Task To Run" /C:"Next Run Time" /C:"Last Run Time" /C:"Status"

echo.
echo 📝 SENASTE LOGGPOSTER:
if exist podcast_log.txt (
    echo Visar sista 5 körningarna:
    powershell "Get-Content podcast_log.txt | Select-Object -Last 5"
) else (
    echo Ingen loggfil hittad än.
)

echo.
echo 📁 SENASTE GENERERADE FILER:
echo Audio-filer:
powershell "Get-ChildItem *.mp3 -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | Select-Object Name"
echo.
echo Script-filer:
powershell "Get-ChildItem *script*.txt -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | Select-Object Name"

echo.
echo 🔧 MANUELL KÖRNING:
echo För att köra manuellt: .\run_podcast.bat
echo För att testa schemaläggning: schtasks /run /tn "ManniskaMaskinMiljo_WeeklyPodcast"

echo.
pause
