@echo off
chcp 65001 > nul
echo.
echo ===============================================
echo AUTOMATISK PODCAST NEDLADDNING
echo Startar: %date% %time%
echo ===============================================
echo.

REM Navigera till rätt mapp
cd /d "C:\Users\pontu\Documents\Autopodd\morgonradio"

REM Aktivera virtual environment om det finns
if exist "venv\Scripts\activate.bat" (
    echo Aktiverar virtual environment...
    call venv\Scripts\activate.bat
)

REM Kör episode downloader
echo Startar episode downloader...
python auto_episode_downloader.py

echo.
echo ===============================================
echo Klar: %date% %time%
echo ===============================================
echo.

REM Håll fönstret öppet i 5 sekunder för att se resultat
timeout /t 5 > nul
