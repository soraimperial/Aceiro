@echo off
cd /d "%~dp0"

set "PYCMD=py -3"
%PYCMD% --version >nul 2>nul || set "PYCMD=python"
%PYCMD% --version >nul 2>nul || (echo Python nao encontrado. Instale-o em python.org e tente de novo. & pause & exit /b 1)

if not exist venv (%PYCMD% -m venv venv)
call venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
if errorlevel 1 (
  echo.
  echo Ocorreu um erro ao correr o Aceiro ^(ver mensagens acima^).
  pause
)
