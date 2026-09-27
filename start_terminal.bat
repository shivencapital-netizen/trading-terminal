@echo off
title Trading Terminal - Startup

echo ============================================
echo   STARTING TRADING TERMINAL (Backend + UI)
echo ============================================

REM ---- Start or reuse the local Ollama service ----
echo Checking local Ollama service...
call :check_ollama
if not errorlevel 1 goto ollama_ready

set "OLLAMA_EXE="
for /f "delims=" %%I in ('where ollama 2^>nul') do if not defined OLLAMA_EXE set "OLLAMA_EXE=%%I"
if not defined OLLAMA_EXE if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if not defined OLLAMA_EXE if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA_EXE=%ProgramFiles%\Ollama\ollama.exe"

if not defined OLLAMA_EXE (
    echo WARNING: Ollama was not found. The app will start, but Backtest Lab AI will be unavailable.
    goto start_terminal
)

REM Do not start a second Ollama server when its process is already running.
tasklist 2>nul | findstr /I /C:"ollama.exe" /C:"ollama app.exe" >nul
if errorlevel 1 (
    echo Starting Ollama local model service...
    start "Ollama Local AI" /min "%OLLAMA_EXE%" serve
) else (
    echo Ollama is already running; waiting for its API...
)

set "OLLAMA_WAIT_COUNT=0"
:wait_for_ollama
call :check_ollama
if not errorlevel 1 goto ollama_ready
set /a OLLAMA_WAIT_COUNT+=1
if %OLLAMA_WAIT_COUNT% GEQ 15 goto ollama_timeout
timeout /t 2 /nobreak >nul
goto wait_for_ollama

:ollama_timeout
echo WARNING: Ollama did not become ready within 30 seconds.
echo The Trading Terminal will still start; Backtest Lab AI may be unavailable.
goto start_terminal

:ollama_ready
echo Ollama API is ready.
curl.exe --silent --fail --max-time 2 "http://127.0.0.1:11434/api/tags" | findstr /I /C:"qwen3:4b" >nul
if errorlevel 1 echo WARNING: qwen3:4b is not downloaded. Run "ollama pull qwen3:4b" before using Backtest Lab.

:start_terminal
REM ---- Start Backend (FastAPI + Ingestion) ----
echo Starting backend...
start cmd /k "cd /d D:\trading_terminal\backend && ..\venv\Scripts\activate && python -m uvicorn app.main:app --reload"

REM ---- Start Frontend (React) ----
echo Starting frontend...
start cmd /k "cd frontend && npm start"

echo ============================================
echo   STARTUP REQUESTS SENT (see any warnings above)
echo ============================================
exit /b 0

:check_ollama
curl.exe --silent --show-error --fail --max-time 2 "http://127.0.0.1:11434/api/tags" >nul 2>&1
exit /b %ERRORLEVEL%
