@echo off
TITLE Multiprocess Launcher

:: Domyslne wartosci (0 = nie uruchamiaj, 1 = uruchamiaj)
set RUN_XTTS=0
set RUN_QWEN=0
set RUN_OMNI=0
set RUN_HIGGS=0

:: Jesli nie podano zadnych argumentow, uruchamiamy wszystko (tryb domyslny)
if "%~1"=="" (
    echo Brak argumentow. Uruchamiam wszystkie serwisy...
    set RUN_XTTS=1
    set RUN_QWEN=1
    set RUN_OMNI=1
    set RUN_HIGGS=1
    goto run_services
)

echo Uruchamianie w trybie selektywnym...

:: Zbieranie i sprawdzanie argumentow
:parse_args
if "%~1"=="" goto run_services
if /I "%~1"=="--xtts" set RUN_XTTS=1
if /I "%~1"=="--qwen" set RUN_QWEN=1
if /I "%~1"=="--omnivoice" set RUN_OMNI=1
if /I "%~1"=="--higgs" set RUN_HIGGS=1
if /I "%~1"=="--all" (
    set RUN_XTTS=1
    set RUN_QWEN=1
    set RUN_OMNI=1
    set RUN_HIGGS=1
)
shift
goto parse_args

:run_services
echo.

:: 1. BACKEND API (Uruchamiany zawsze, bo jest rdzeniem aplikacji)
echo [START] Backend API...
start "Backend" cmd /k "call conda activate ABApi && uvicorn main:app --port 8000"

:: 2. XTTS
if %RUN_XTTS%==1 (
    echo [START] XTTS...
    start "XTTS" cmd /k "call conda activate Audiobook3.10 && uvicorn workers.xtts_worker:app --port 8001"
)

:: 3. QWEN
if %RUN_QWEN%==1 (
    echo [START] Qwen...
    start "Qwen" cmd /k "call conda activate ABqwen3.12 && uvicorn workers.qwen_worker:app --port 8002"
)

:: 4. OMNIVOICE
if %RUN_OMNI%==1 (
    echo [START] Omnivoice...
    start "Omnivoice" cmd /k "call conda activate ABOmnivoice && uvicorn workers.omnivoice_worker:app --port 8003"
)

echo.
echo Gotowe! Wybrane procesy zostaly poprawnie zainicjowane.