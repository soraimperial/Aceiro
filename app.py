"""
Aceiro — registo pessoal (e de pequena equipa) de horas de trabalho.

Aplicação local: um pequeno servidor Flask serve a interface (static/index.html)
e guarda os dados em ficheiros JSON simples nesta mesma pasta. Se essa pasta
estiver dentro do OneDrive/SharePoint, os dados sincronizam como qualquer outro
ficheiro — mas evite ter a aplicação aberta em dois computadores ao mesmo tempo
(ver README.txt).

Suporta vários "utilizadores" (perfis) dentro da mesma instalação — cada um com
o seu próprio ficheiro de dados (dados-<utilizador>.json) — para quem quiser
usar o Aceiro para acompanhar uma pequena equipa a partir de um único sítio.
"""
import json
import os
import re
import socket
import sys
import threading
import time
import unicodedata
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

# Quando corre via pythonw.exe (sem consola — ver AbrirAceiro.vbs) ou dentro de
# um .exe empacotado com --windowed, sys.stdout e sys.stderr ficam a None, e
# qualquer print() rebentaria a aplicação.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Quando empacotado com o PyInstaller (ver ConstruirExeParaColegas.bat) o app
# corre "congelado": os ficheiros da interface (static/) ficam num sítio
# temporário interno, mas os dados devem continuar junto ao próprio .exe, para
# ficarem portáteis.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    STATIC_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR)) / "static"
else:
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR / "static"

LEGACY_DATA_FILE = BASE_DIR / "dados.json"  # de antes de existirem utilizadores
USERS_FILE = BASE_DIR / "utilizadores.json"  # lista partilhada de perfis (pode estar num OneDrive/SharePoint)
PORT = 8877


def _local_config_dir():
    # Sítio LOCAL a este computador (nunca dentro da pasta partilhada), para
    # guardar qual foi o último utilizador aberto NESTE PC — se isto ficasse
    # dentro da pasta sincronizada, cada colega "roubaria" a seleção dos
    # outros sempre que o OneDrive sincronizasse.
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".config")
    d = Path(base) / "Aceiro"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return BASE_DIR
    return d


LAST_USER_FILE = _local_config_dir() / "ultimo-utilizador.json"

DEFAULT_STATE = {
    "version": 3,
    "entries": [],
    "shifts": [],
    "clock": None,
    "settings": {"dayTypeOverrides": {}},
}
DEFAULT_USER_NAME = "Eu"

# Rótulos de tipo de tarefa (usados só na exportação CSV, para ficar legível
# no Excel). Os registos guardam internamente o código "ncr"/"outros" — ver
# normalize_type_code, que também aceita os nomes antigos "NCR"/"Outros" para
# ficheiros gravados antes desta mudança de nomes.
TYPE_LABELS = {"ncr": "Trabalho Corrente", "outros": "Trabalho Ad Hoc"}


def normalize_type_code(raw):
    t = str(raw or "").strip().lower()
    if t == "ncr" or "corrente" in t:
        return "ncr"
    return "outros"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


# ---------- utilizadores (perfis) ----------
def slugify(name):
    name = (name or "").strip()
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(c for c in normalized if not unicodedata.combining(c))
    ascii_name = ascii_name.lower()
    ascii_name = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")
    return ascii_name or "utilizador"


def unique_slug(base, existing_slugs):
    if base not in existing_slugs:
        return base
    n = 2
    while "{}-{}".format(base, n) in existing_slugs:
        n += 1
    return "{}-{}".format(base, n)


def user_data_file(slug):
    return BASE_DIR / "dados-{}.json".format(slug)


def atomic_write_json(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save_users(registry):
    # Só a lista partilhada de perfis. Nunca grava aqui qual está "atual" --
    # isso é local a este computador (ver LAST_USER_FILE).
    atomic_write_json(USERS_FILE, {"users": registry["users"]})


def get_registry():
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = None
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            return {"users": data["users"]}

    # Primeira vez que corre com o sistema de utilizadores. Se já existir um
    # dados.json de antes de existirem perfis, migra-o para um primeiro
    # perfil "Eu" sem apagar nada; caso contrário começa mesmo vazio -- não
    # cria automaticamente nenhum utilizador, para não ficar um "Eu"
    # confuso quando a pasta é partilhada com uma equipa.
    if LEGACY_DATA_FILE.exists():
        slug = slugify(DEFAULT_USER_NAME)
        target = user_data_file(slug)
        if not target.exists():
            try:
                with open(LEGACY_DATA_FILE, "r", encoding="utf-8") as f:
                    legacy = json.load(f)
                atomic_write_json(target, legacy)
            except (json.JSONDecodeError, OSError):
                atomic_write_json(target, DEFAULT_STATE)
        registry = {"users": [{"name": DEFAULT_USER_NAME, "slug": slug}]}
    else:
        registry = {"users": []}
    save_users(registry)
    return registry


def local_current_slug(registry):
    # Qual foi o último perfil usado NESTE computador -- guardado fora da
    # pasta partilhada, por isso não se mistura com a escolha dos colegas.
    if LAST_USER_FILE.exists():
        try:
            with open(LAST_USER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            slug = data.get("slug")
        except (json.JSONDecodeError, OSError):
            slug = None
        if slug in [u["slug"] for u in registry["users"]]:
            return slug
    return None


def set_local_current(slug):
    atomic_write_json(LAST_USER_FILE, {"slug": slug})


# ---------- dados (por utilizador) ----------
def load_state_for(slug):
    path = user_data_file(slug)
    if not path.exists():
        atomic_write_json(path, DEFAULT_STATE)
        return dict(DEFAULT_STATE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Ficheiro corrompido ou ilegível (ex.: interrompido a meio de uma
        # sincronização) — guarda-se de lado em vez de se perder, e a app
        # arranca com dados vazios em vez de rebentar.
        try:
            backup = path.with_suffix(".json.corrompido")
            path.replace(backup)
        except OSError:
            pass
        atomic_write_json(path, DEFAULT_STATE)
        return dict(DEFAULT_STATE)

    if not isinstance(data, dict):
        return dict(DEFAULT_STATE)
    data.setdefault("entries", [])
    data.setdefault("shifts", [])
    data.setdefault("clock", None)
    data.setdefault("settings", {"dayTypeOverrides": {}})
    data["settings"].setdefault("dayTypeOverrides", {})
    return data


def save_state_for(slug, state):
    # Escrita atómica: grava num ficheiro temporário e só depois substitui o
    # definitivo, para nunca deixar o ficheiro a meio de uma escrita (o que
    # seria especialmente mau se o OneDrive tentasse sincronizar nesse instante).
    atomic_write_json(user_data_file(slug), state)


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/users", methods=["GET"])
def get_users():
    registry = get_registry()
    return jsonify({"users": registry["users"], "current": local_current_slug(registry)})


@app.route("/api/users", methods=["POST"])
def create_user():
    body = request.get_json(force=True, silent=True) or {}
    name = str(body.get("name", "")).strip()
    if not name:
        return jsonify({"error": "nome em falta"}), 400

    registry = get_registry()
    for u in registry["users"]:
        if u["name"].strip().lower() == name.lower():
            set_local_current(u["slug"])
            return jsonify({"users": registry["users"], "current": u["slug"]})

    existing_slugs = [u["slug"] for u in registry["users"]]
    slug = unique_slug(slugify(name), existing_slugs)
    save_state_for(slug, DEFAULT_STATE)
    registry["users"].append({"name": name, "slug": slug})
    save_users(registry)
    set_local_current(slug)
    return jsonify({"users": registry["users"], "current": slug})


@app.route("/api/users/select", methods=["POST"])
def select_user():
    body = request.get_json(force=True, silent=True) or {}
    slug = str(body.get("slug", ""))
    registry = get_registry()
    if slug not in [u["slug"] for u in registry["users"]]:
        return jsonify({"error": "utilizador desconhecido"}), 404
    set_local_current(slug)
    return jsonify({"users": registry["users"], "current": slug})


@app.route("/api/state", methods=["GET"])
def get_state():
    registry = get_registry()
    slug = local_current_slug(registry)
    if not slug:
        return jsonify({"error": "no-user"}), 409
    return jsonify(load_state_for(slug))


@app.route("/api/state", methods=["POST"])
def post_state():
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid"}), 400
    registry = get_registry()
    slug = local_current_slug(registry)
    if not slug:
        return jsonify({"error": "no-user"}), 409
    save_state_for(slug, data)
    return jsonify({"ok": True})


@app.route("/api/export", methods=["POST"])
def export_csv():
    registry = get_registry()
    slug = local_current_slug(registry)
    if not slug:
        return jsonify({"error": "no-user"}), 409
    state = load_state_for(slug)
    rows = ["Data;Tipo;Tarefa;Horas"]
    entries = sorted(state.get("entries", []), key=lambda e: e.get("date", ""))
    for e in entries:
        task = str(e.get("task", "")).replace(";", ",")
        hours = str(e.get("hours", "")).replace(".", ",")
        type_label = TYPE_LABELS.get(normalize_type_code(e.get("type", "")), e.get("type", ""))
        rows.append("{};{};{};{}".format(e.get("date", ""), type_label, task, hours))
    csv_text = "\r\n".join(rows)
    out_path = BASE_DIR / "aceiro-export-{}.csv".format(slug)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(csv_text)
    return jsonify({"ok": True, "path": str(out_path)})


def _port_is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _run_flask():
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


def _open_in_browser(url):
    webbrowser.open(url)
    # Quando aberto sem consola (pythonw, ou um .exe --windowed) não há onde
    # escrever nem um Enter para premir — nesse caso fica apenas a correr em
    # segundo plano, e fecha-se fechando a aba do browser e terminando o
    # processo pelo Gestor de Tarefas, se necessário. Com consola disponível
    # (ex.: IniciarAceiro.bat), pede Enter para sair de forma limpa.
    if sys.stdin is not None and sys.stdin.isatty():
        input("Aceiro está a correr em " + url + " — prima Enter aqui para fechar...")
    else:
        while True:
            time.sleep(3600)


def main():
    print("A iniciar o Aceiro...")
    t = threading.Thread(target=_run_flask, daemon=True)
    t.start()

    for _ in range(50):  # espera até ~5s pelo arranque do servidor local
        if _port_is_open(PORT):
            break
        time.sleep(0.1)

    url = "http://127.0.0.1:{}".format(PORT)

    try:
        import webview
    except ImportError:
        print("'pywebview' não está instalado — a abrir no browser.")
        _open_in_browser(url)
        return

    try:
        webview.create_window("Aceiro", url, width=1040, height=920, min_size=(760, 640))
        webview.start()
    except Exception as e:
        # Normalmente falta o WebView2 Runtime da Microsoft neste computador.
        # Em vez de ficar preso, abre a mesma aplicação no browser normal.
        print("Não consegui abrir a janela própria ({}) — a abrir no browser.".format(e))
        _open_in_browser(url)


if __name__ == "__main__":
    main()
