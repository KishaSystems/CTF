@echo off
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    py build.py
) else (
    python build.py
)
if "%~1"=="" pause
