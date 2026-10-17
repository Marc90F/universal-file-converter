@echo off
setlocal
cd /d "%~dp0"
title Convertitore Universale Desktop

echo ========================================================
echo       UNIVERSAL FILE CONVERTER - CONVERTITORE UNIVERSALE       
echo ========================================================
echo.
echo Controllo ambiente Python in corso...

set "PY_CMD="

:: 1. Prova il comando python generico
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :START_APP
)

:: 2. Prova il launcher ufficiale py di Windows
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :START_APP
)

:: 3. Controlla percorsi noti in LocalAppData
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :START_APP
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :START_APP
)

echo.
echo [ERRORE] Python non e' stato trovato nel sistema.
echo Scarica e installa Python da: https://www.python.org/downloads/
echo Ricordati di spuntare "Add Python to PATH" durante l'installazione.
echo.
pause
exit /b 1

:START_APP
echo [OK] Python rilevato: %PY_CMD%
echo.
echo Avvio interfaccia Universal File Converter...
"%PY_CMD%" main.py %*

if %errorlevel% neq 0 (
    echo.
    echo Si e' verificato un problema durante l'esecuzione.
    pause
)
