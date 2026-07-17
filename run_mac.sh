#!/bin/bash

echo "Installing Frontend requirements..."
cd frontend
npm install
cd ..

echo "Activating virtual environment and starting backend..."
./venv_ev_nexus/bin/uvicorn api:app --reload &
BACKEND_PID=$!

# Assicura che il processo backend venga ucciso (inclusi i child worker del --reload)
trap "echo 'Fermando i servizi...'; pkill -f uvicorn 2>/dev/null; lsof -t -i:8000 | xargs kill -9 2>/dev/null; exit 0" EXIT INT TERM

echo "Starting frontend..."
cd frontend
npm run dev
