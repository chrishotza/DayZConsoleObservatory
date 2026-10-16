@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0launcher.py"
    goto end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0launcher.py"
    goto end
)
echo Python 3.10+ is required. Install it, then double-click START_HERE.cmd again.
echo https://www.python.org/downloads/
pause
:end
endlocal
