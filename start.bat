@echo off
setlocal
title KISS Studio Launcher
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python not found. Install it from https://python.org and re-run.
    pause & exit /b 1
)

python -c "import dotenv" >nul 2>nul
if errorlevel 1 (
    echo Installing python-dotenv ^(one-time^)...
    python -m pip install --quiet python-dotenv
)

echo.
echo  ============================================
echo    KISS STUDIO - Agents League Hackathon
echo  ============================================
echo.
echo    [1] Command Center dashboard  (recommended)
echo    [2] Track 2 reasoning demo    (terminal)
echo    [3] Fantasy Campaign template (optional - isolated example)
echo    [4] Vision board for creator-launch
echo    [5] Teams governance mock     (browser)
echo    [6] Builder Studio            (advanced + KISS IQ)
echo.
set /p choice="  Pick 1-6 and press Enter [1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo  Starting Command Center at http://localhost:8765 ...
    start "" http://localhost:8765
    cd command-center
    python server.py
) else if "%choice%"=="2" (
    cd foundry-track2
    python main.py
    echo.
    pause
) else if "%choice%"=="3" (
    cd creative-track1\fantasy-template
    python campaign_studio.py --preset
    echo.
    echo  Output: creative-track1\fantasy-template\output\ember-tides\
    echo  (Optional side template - fully isolated; affects no other project.)
    pause
) else if "%choice%"=="4" (
    cd creative-track1
    python visualize.py ..\demo-project\creator-launch
    start "" "..\demo-project\creator-launch\vision\vision_board.svg"
    pause
) else if "%choice%"=="5" (
    cd m365-track3\mock-ui
    python build_mock.py
    start "" teams-mock.html
    pause
) else if "%choice%"=="6" (
    echo.
    echo  Starting Builder Studio at http://localhost:8765/builder ...
    start "" http://localhost:8765/builder
    cd command-center
    python server.py
) else (
    echo  Unknown choice.
    pause
)
endlocal
