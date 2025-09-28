@echo off
chcp 65001 > nul
echo.
echo ===============================================
echo SMART PODCAST MONITOR 
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

REM Kör smart episode monitor
echo Startar smart episode monitor...
python smart_episode_monitor.py

echo.
echo ===============================================
echo Klar: %date% %time%
echo ===============================================
echo.

REM Håll fönstret öppet i 3 sekunder
timeout /t 3 > nul
