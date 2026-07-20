# RFID-Musikbox

Eigenständig entwickelte RFID-Musikbox für ältere Menschen, gebaut auf einem
Raspberry Pi 3B mit Raspberry Pi OS Lite (Debian 13 "Trixie"). Bewusst als
Eigenentwicklung statt Phoniebox (RPi-Jukebox-RFID), um die Software
vollständig zu verstehen, selbst zu kontrollieren und Kompatibilitätsprobleme
mit Trixie zu vermeiden.

## Funktionsweise (Muss-Features)

- Karte auflegen → zugeordneter Ordner (= ein Album) startet von Track 1
- Karte wegnehmen → Wiedergabe stoppt komplett (kein Pause-Zustand)
- Karte erneut auflegen → Ordner startet immer wieder von vorne (kein Resume)
- Web-Interface zum Verwalten der Karten-Zuordnungen (Scannen, Zuweisen,
  Löschen, Übersicht)
- Zusätzliches Test-Feature im Web-Interface: Ordner ohne Karte probeweise
  abspielen/stoppen, zum Prüfen der Audio-Ausgabe ohne RFID-Reader

Explizit **nicht** enthalten (bewusste Entscheidung): physische Buttons,
Mehrsprachigkeit, Podcast-Feeds, Bluetooth-Pairing, Coverbilder,
Shutdown-Timer/Fade-out.

## Architektur

Vier unabhängige Bausteine, damit sich später z.B. physische Buttons sauber
nachrüsten lassen, ohne bestehende Teile anzufassen:

RFID-Daemon (daemon.py)
├── liest UID über reader.py (RFIDReader-Interface)
├── schlägt Ordner in storage.py nach (MappingStorage)
├── steuert Wiedergabe über player.py (Player-Interface)
└── schreibt zuletzt gesehene UID in data/last_seen_uid.json

Web-Interface (webapp.py, Flask)
├── liest/schreibt Zuordnungen über storage.py (dieselbe Klasse wie oben)
├── liest data/last_seen_uid.json, um die zuletzt gescannte UID anzuzeigen
└── Test-Play-Feature: spielt/stoppt einen Ordner direkt über MPD, ohne
Karte oder Daemon (zum Testen der Audio-Kette)


**Warum kein direkter Reader-Zugriff im Web-Interface?** RC522 spricht über
SPI, das i.d.R. nur exklusiv von einem Prozess genutzt werden kann. Deshalb
liest ausschließlich `daemon.py` den Reader; das Web-Interface liest nur die
Datei, die der Daemon schreibt.

### Module im Detail

| Datei | Zweck | Status |
|---|---|---|
| `player.py` | `Player`-Interface + `MPDPlayer` (echt, via MPD) + `FakePlayer` (Test) | ✅ fertig, getestet |
| `reader.py` | `RFIDReader`-Interface + `MFRC522Reader` (echt, SPI) + `FakeReader` (Test) | ✅ fertig, getestet |
| `storage.py` | `MappingStorage`: JSON-Datei (UID → Ordner) mit File-Lock für gleichzeitigen Zugriff | ✅ fertig, getestet |
| `daemon.py` | Hauptschleife: pollt Reader, steuert Player, mit Debouncing (4 leere Polls à 1s bevor "Karte weg" gilt) | ✅ fertig, getestet |
| `webapp.py` | Flask-Interface zum Verwalten der Zuordnungen + Test-Play-Feature | ✅ fertig, auf dem Pi mit echter Audio-Ausgabe getestet |

## Warum testbar ohne Hardware?

Sowohl `player.py` als auch `reader.py` haben zwei Implementierungen: eine
echte (`MPDPlayer`, `MFRC522Reader`) und eine `Fake`-Version, die sich exakt
wie das Interface verhält, aber keine echte Hardware braucht. Der
`mfrc522`-Import in `reader.py` passiert bewusst erst innerhalb von
`MFRC522Reader.__init__`, damit die Datei auch auf Windows importierbar
bleibt (solange man `MFRC522Reader` nicht tatsächlich instanziiert).

Dadurch lässt sich die komplette Kernlogik (`daemon.py`, `storage.py`) auf
einem normalen Windows-PC mit `pytest` durchtesten, ganz ohne Pi oder
RC522-Reader.

## Setup (lokal, Windows, zum Weiterentwickeln ohne Hardware)

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install python-mpd2 filelock pytest flask
```

Tests ausführen:
```powershell
pytest test/ -v
```

Web-Interface lokal starten (Testordner `test-musik/` mit ein paar leeren
Unterordnern anlegen, deren Namen als Alben im Dropdown erscheinen):
```powershell
$env:RFID_MUSIC_DIR = "test-musik"
$env:RFID_MAPPINGS_FILE = "data/mappings.json"
$env:RFID_LAST_SEEN_FILE = "data/last_seen_uid.json"
py webapp.py
```
Dann im Browser `http://localhost:5000` öffnen.

## Setup auf dem Pi (Stand: eingerichtet, ohne RFID-Reader getestet)

```bash
cd /home/pi
git clone https://github.com/DEIN-USERNAME/rfid-musikbox.git
cd rfid-musikbox
python3 -m venv venv
source venv/bin/activate
pip install python-mpd2 filelock flask
mkdir -p /home/pi/rfid-musikbox-data
```

Web-Interface starten:
```bash
export RFID_MUSIC_DIR="/home/pi/musik"
export RFID_MAPPINGS_FILE="/home/pi/rfid-musikbox-data/mappings.json"
export RFID_LAST_SEEN_FILE="/home/pi/rfid-musikbox-data/last_seen_uid.json"
python webapp.py
```
Danach von einem anderen Rechner im selben Netzwerk erreichbar unter
`http://<Pi-IP>:5000`.

## System-Konfiguration auf dem Pi (außerhalb des Projekts)

Diese Änderungen liegen außerhalb des Git-Repos (Systemkonfiguration des Pi
selbst) und müssten bei einem Neuaufsetzen des Pi wiederholt werden.

**Alte Phoniebox-Installation entfernt:**
- Services gestoppt/deaktiviert: `phoniebox-gpio-control`,
  `phoniebox-idle-watchdog`, `phoniebox-rfid-reader`,
  `phoniebox-startup-scripts`, `lighttpd`
- Ordner `/home/pi/RPi-Jukebox-RFID` gelöscht
- Keine Cronjobs oder sudoers-Einträge von Phoniebox gefunden (geprüft und
  sauber)

**MPD-Konfiguration** (`/etc/mpd.conf`), Zeile mit `music_directory`
angepasst, da sie noch auf den gelöschten Phoniebox-Ordner zeigte:

music_directory "/home/pi/musik"

Danach `sudo systemctl restart mpd` und `mpc update`, damit MPD den neuen
Pfad übernimmt und seine Musik-Datenbank neu einliest.

Offen/noch nicht behoben: `playlist_directory` in derselben Datei zeigt
vermutlich noch auf den alten Phoniebox-Pfad (führt beim MPD-Start zu einer
harmlosen Fehlermeldung, blockiert aber nichts, da Playlists nicht genutzt
werden).

**Samba-Konfiguration** (`/etc/samba/smb.conf`):
- Alte Freigaben `[phoniebox]` und `[phoniebox_audiofile]` auskommentiert
  (zeigten auf den gelöschten Phoniebox-Ordner)
- Neue eigene Freigabe hinzugefügt:

[musik]
comment = RFID Musikbox
path = /home/pi/musik
browseable = Yes
writeable = Yes
only guest = no

- Samba-Passwort für den Nutzer `pi` neu gesetzt (separat vom
  Linux-Login-Passwort): `sudo smbpasswd -a pi`
- Danach `sudo systemctl restart smbd`

Musik-Ordner ist von Windows aus erreichbar unter `\\<Pi-IP>\musik`.

## Noch offen / nächste Schritte (sobald RC522 angeschlossen ist)

- [ ] RC522 per SPI mit dem Pi verkabeln (Breadboard/Jumper-Kabel, kein Löten)
- [ ] SPI auf dem Pi aktivieren (`raspi-config`)
- [ ] `mfrc522`-Bibliothek auf dem Pi installieren
- [ ] `daemon.py` als systemd-Service einrichten (automatischer Neustart nach
  Stromausfall/Absturz)
- [ ] `webapp.py` ebenfalls als systemd-Service oder zumindest dauerhaft
  laufend einrichten
- [ ] Ersten echten Hardware-Test: Karte auflegen → Wiedergabe, Karte weg →
  Stopp
- [ ] Optional: `playlist_directory` in `/etc/mpd.conf` aufräumen

## Später denkbar (aktuell nicht gebaut, Architektur lässt es aber zu)

- Physische Play/Pause-Steuerung (eigener, unabhängiger Baustein, würde nur
  `player.py` ansprechen)
- Spotify-Integration, Streaming-Radio