import os
import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
from storage import MappingStorage
from player import MPDPlayer

MPD_HOST = os.environ.get("RFID_MPD_HOST", "localhost")
MPD_PORT = int(os.environ.get("RFID_MPD_PORT", "6600"))


def get_player() -> MPDPlayer | None:
    """Baut bei Bedarf eine MPD-Verbindung auf. Gibt None zurück, falls MPD nicht erreichbar ist."""
    try:
        return MPDPlayer(host=MPD_HOST, port=MPD_PORT)
    except Exception as e:
        print(f"[webapp] Konnte nicht mit MPD verbinden: {e}")
        return None

# Pfade über Umgebungsvariablen konfigurierbar (Standardwerte = Pi-Pfade fürs Produktivsystem)
MUSIC_DIR = os.environ.get("RFID_MUSIC_DIR", "/home/pi/musik")
MAPPINGS_FILE = os.environ.get("RFID_MAPPINGS_FILE", "/home/pi/rfid-musikbox-data/mappings.json")
LAST_SEEN_UID_FILE = os.environ.get("RFID_LAST_SEEN_FILE", "data/last_seen_uid.json")

app = Flask(__name__)
storage = MappingStorage(MAPPINGS_FILE)


def get_music_folders() -> list[str]:
    """Liest alle Unterordner im Musik-Verzeichnis (= verfügbare Alben)."""
    music_path = Path(MUSIC_DIR)
    if not music_path.exists():
        return []
    return sorted(f.name for f in music_path.iterdir() if f.is_dir())


def get_last_seen_uid() -> str | None:
    """Liest die zuletzt vom Daemon erkannte UID aus, falls vorhanden."""
    path = Path(LAST_SEEN_UID_FILE)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("uid")


@app.route("/")
def index():
    return render_template(
        "index.html",
        mappings=storage.list_mappings(),
        folders=get_music_folders(),
        last_seen_uid=get_last_seen_uid(),
    )


@app.route("/assign", methods=["POST"])
def assign():
    uid = request.form.get("uid")
    folder = request.form.get("folder")
    if uid and folder:
        storage.set_mapping(uid, folder)
    return redirect(url_for("index"))


@app.route("/delete/<uid>", methods=["POST"])
def delete(uid):
    storage.delete_mapping(uid)
    return redirect(url_for("index"))

@app.route("/test-play/<folder>", methods=["POST"])
def test_play(folder):
    player = get_player()
    if player:
        player.play_folder(folder)
    return redirect(url_for("index"))


@app.route("/test-stop", methods=["POST"])
def test_stop():
    player = get_player()
    if player:
        player.stop()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)