@echo off
title Trading Terminal - Shutdown

echo ============================================
echo   STOPPING TRADING TERMINAL
echo ============================================

REM ---- Kill FastAPI backend (uvicorn + python) ----
echo Stopping backend...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

REM ---- Kill React frontend (node) ----
echo Stopping frontend...
taskkill /F /IM node.exe >nul 2>&1

REM ---- Kill any ingestion or background workers (optional future-proofing) ----
echo Stopping background workers...
taskkill /F /IM celery.exe >nul 2>&1
taskkill /F /IM rq.exe >nul 2>&1

echo ============================================
echo   ALL SERVICES STOPPED
echo ============================================
pause
