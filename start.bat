@echo off
PUSHD "%~dp0"
setlocal

if not exist ".venv\" (
    echo First install...

    call python -m venv .venv
    call .venv\Scripts\activate.bat & pip install -r requirements.txt
)

call .venv\Scripts\activate.bat & python main.py

pause
exit /b

