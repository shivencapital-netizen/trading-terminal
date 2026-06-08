@echo off
title Trading Terminal - Startup

echo ============================================
echo   STARTING TRADING TERMINAL (Backend + UI)
echo ============================================

REM ---- Start Backend (FastAPI + Ingestion) ----
echo Starting backend...
start cmd /k "cd /d D:\trading_terminal\backend && ..\venv\Scripts\activate && python -m uvicorn app.main:app --reload"

REM ---- Start Frontend (React) ----
echo Starting frontend...
start cmd /k "cd frontend && npm start"

echo ============================================
echo   ALL SERVICES STARTED SUCCESSFULLY
echo ============================================
