#!/usr/bin/env bash
# Gera um binário único do Aceiro para Linux (equivalente ao Aceiro.exe do
# Windows) -- um único ficheiro, sem precisar de Python instalado no
# computador de quem o recebe.
#
# Corre-se UMA VEZ, num computador Linux com Python instalado. Não é
# possível gerar o binário de Linux a partir do Windows (nem o inverso) --
# o PyInstaller tem de correr no mesmo sistema operativo do resultado. Se
# não tiver um Linux à mão, veja o workflow em
# .github/workflows/build.yml, que gera as duas versões automaticamente
# no GitHub, sem precisar de nenhum computador Linux próprio.
set -e
cd "$(dirname "$0")"

PYCMD=python3
command -v "$PYCMD" >/dev/null 2>&1 || PYCMD=python
command -v "$PYCMD" >/dev/null 2>&1 || {
    echo "Python 3 não encontrado. Instale-o (ex.: 'sudo apt install python3 python3-venv') e tente de novo."
    exit 1
}

[ -d venv-linux ] || "$PYCMD" -m venv venv-linux
source venv-linux/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt pyinstaller

rm -rf build dist

pyinstaller --noconfirm --clean --onefile --name Aceiro --add-data "static:static" app.py
chmod +x dist/Aceiro

cat <<'EOF'

============================================================
Pronto! O ficheiro único está em: dist/Aceiro

Para enviar a colegas: basta esse UM ficheiro (dist/Aceiro) -- por
email, pen, OneDrive, o que for mais fácil. Cada colega só precisa de
lhe dar permissão de execução (clique direito > Propriedades >
Permissões > "Permitir executar", ou "chmod +x Aceiro" num terminal) e
fazer duplo clique / correr no terminal -- não precisam de instalar
Python nem mais nada.

Sobre a janela própria da aplicação (em vez de abrir no browser): isso
depende do WebKitGTK estar instalado no computador de quem o recebe --
já vem pronto na maioria das distribuições de ambiente de trabalho
(GNOME, etc.), mas não em todas. Se não estiver, o Aceiro deteta isso
sozinho e abre automaticamente no browser normal em vez de falhar --
continua a funcionar na mesma, só que numa aba do browser em vez de
numa janela própria. Não é preciso Wine nem nenhum emulador do Windows
para nenhum dos dois casos.
============================================================
EOF
