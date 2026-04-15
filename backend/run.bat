@echo off
TITLE Multiprocess Launcher

:: Run from anaconda prompt console

:: 1. XTTS
start "XTTS" cmd /k "call conda activate Audiobook3.10 && uvicorn workers.xtts_worker:app --port 8001"

:: 2. QWEN (z Twoim środowiskiem)
start "Qwen" cmd /k "call conda activate ABqwen3.12 && uvicorn workers.qwen_worker:app --port 8002"

:: 3. OMNIVOICE
start "Omnivoice" cmd /k "call conda activate ABOmnivoice && uvicorn workers.omnivoice_worker:app --port 8003"

:: 4. BACKEND API
start "Backend" cmd /k "call conda activate ABApi && uvicorn main:app --port 8000"

echo Wszystkie procesy zostaly zainicjowane.