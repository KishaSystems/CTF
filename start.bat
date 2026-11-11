@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    py ctf.py %*
) else (
    python ctf.py %*
)
if "%~1"=="" pause
