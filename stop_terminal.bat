@echo off
title Trading Terminal - Shutdown

echo ============================================
echo   STOPPING TRADING TERMINAL
echo ============================================

REM Stop only this project's backend/frontend processes to avoid closing unrelated apps.
echo Stopping Trading Terminal backend and frontend...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$root=[IO.Path]::GetFullPath('%~dp0').TrimEnd('\'); $targets=Get-CimInstance Win32_Process | Where-Object { ($_.Name -in @('python.exe','pythonw.exe') -and $_.ExecutablePath -like ($root+'\venv\*') -and $_.CommandLine -match '-m\s+uvicorn\s+app\.main:app') -or ($_.Name -eq 'node.exe' -and $_.CommandLine.Contains($root+'\frontend\node_modules')) }; foreach($target in $targets) { & taskkill.exe /F /T /PID $target.ProcessId 2>$null | Out-Null }"

REM Ollama is a shared local AI service. Leave it running across terminal restarts.
echo Leaving Ollama running for Backtest Lab and future app starts.

echo ============================================
echo   ALL SERVICES STOPPED
echo ============================================
pause
