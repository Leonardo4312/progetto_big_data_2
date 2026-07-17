@echo off
setlocal

echo =======================================================
echo     EV-Nexus - Startup Script for Windows
echo =======================================================
echo.

echo [1/3] Installing Frontend requirements...
cd frontend
call npm install
cd ..
echo.

echo [2/3] Starting Backend (Uvicorn) in a new window...
:: Apre una nuova finestra del prompt per far girare il backend
:: Usa il path corretto per l'ambiente virtuale su Windows
start "EV_Nexus Backend" cmd /c ".\venv_ev_nexus\Scripts\activate && uvicorn api:app --reload"
echo Backend started!
echo.

echo [3/3] Starting Frontend...
cd frontend
call npm run dev
