@echo off
REM Automatisk podcast-generering för Människa Maskin Miljö
REM Körs varje onsdag kl 07:00

echo ===============================================
echo   MÄNNISKA MASKIN MILJÖ - AUTOMATISK KÖRNING
echo   %date% %time%
echo ===============================================

REM Byta till rätt katalog
cd /d "C:\Users\pontu\Documents\Autopodd\morgonradio"

REM Aktivera virtual environment (om du använder det)
REM call venv\Scripts\activate.bat

REM Kör podcast-genereringen
echo Startar podcast-generering...
python src\main.py

REM Kontrollera om det funkade
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ FRAMGÅNG! Podcast-avsnitt genererat
    echo Datum: %date% %time%
) else (
    echo.
    echo ❌ FEL! Podcast-generering misslyckades
    echo Felkod: %ERRORLEVEL%
    echo Datum: %date% %time%
)

REM Logga resultatet
echo %date% %time% - Podcast-generering kördes (Exit code: %ERRORLEVEL%) >> podcast_log.txt

echo.
echo Tryck valfri tangent för att stänga...
pause >nul
