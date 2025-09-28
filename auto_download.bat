@echo off
REM Windows batch-script för automatisk nedladdning av podcast-avsnitt
REM Körs av Windows Task Scheduler

echo %date% %time% - Startar automatisk nedladdning av podcast-avsnitt >> auto_download_log.txt

cd /d "C:\Users\pontu\Documents\Autopodd\morgonradio"

REM Aktivera virtual environment om det finns
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Kör nedladdnings-scriptet
python auto_episode_downloader.py >> auto_download_log.txt 2>&1

echo %date% %time% - Nedladdning klar >> auto_download_log.txt
