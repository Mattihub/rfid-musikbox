import json
import time
from reader import RFIDReader
from player import Player
from storage import MappingStorage

POLL_INTERVAL_SECONDS = 1
EMPTY_POLLS_BEFORE_STOP = 4
LAST_SEEN_UID_FILE = "data/last_seen_uid.json"


def _write_last_seen_uid(uid: str) -> None:
    with open(LAST_SEEN_UID_FILE, "w", encoding="utf-8") as f:
        json.dump({"uid": uid}, f)


def run(
        reader: RFIDReader,
        player: Player,
        storage: MappingStorage,
        poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
) -> None:
    """Haupt-Schleife: pollt den Reader, steuert den Player anhand der Zuordnungen."""
    current_uid: str | None = None
    empty_poll_count = 0

    while True:
        uid = reader.read_uid()

        if uid is not None:
            empty_poll_count = 0

            if uid != current_uid:
                _write_last_seen_uid(uid)

                folder = storage.get_folder_for_uid(uid)
                if folder is not None:
                    player.play_folder(folder)
                    current_uid = uid
                else:
                    print(f"[daemon] Unbekannte UID '{uid}', keine Zuordnung gefunden.")
                    current_uid = uid

        else:
            if current_uid is not None:
                empty_poll_count += 1
                if empty_poll_count >= EMPTY_POLLS_BEFORE_STOP:
                    player.stop()
                    current_uid = None
                    empty_poll_count = 0

        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    from reader import MFRC522Reader
    from player import MPDPlayer

    real_reader = MFRC522Reader()
    real_player = MPDPlayer()
    real_storage = MappingStorage("/home/pi/rfid-musikbox-data/mappings.json")

    run(real_reader, real_player, real_storage)