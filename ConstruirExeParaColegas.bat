@echo off
cd /d "%~dp0"

rem Este ficheiro nao e para uso diario. Corre-se UMA VEZ (neste computador,
rem onde ja tem Python instalado) para gerar um Aceiro.exe portatil que pode
rem enviar aos colegas -- eles nao precisam de instalar Python nem nada.

set "PYCMD=py -3"
%PYCMD% --version >nul 2>nul || set "PYCMD=python"
%PYCMD% --version >nul 2>nul || (echo Python nao encontrado. Instale-o em python.org e tente de novo. & pause & exit /b 1)

if not exist venv (%PYCMD% -m venv venv)
call venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pyinstaller

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller --noconfirm --clean --windowed --onefile --name Aceiro --add-data "static;static" app.py

echo.
echo ============================================================
echo Pronto! O ficheiro unico esta em: dist\Aceiro.exe
echo.
echo Para enviar aos colegas: basta esse UM ficheiro (Aceiro.exe) --
echo por email, Teams, pen, OneDrive, o que for mais facil. Cada
echo colega so precisa de o colocar numa pasta a gosto e fazer duplo
echo clique -- nao precisam de instalar Python nem mais nada, nem
echo veem ficheiros bat/vbs/pastas por tras. Da primeira vez que
echo abrirem cria-se ali, ao lado do Aceiro.exe, o dados do proprio
echo colega -- pode ser movido/copiado para outra pasta se preferirem
echo arrumar, desde que o dados fique sempre ao lado do Aceiro.exe.
echo ============================================================
pause
