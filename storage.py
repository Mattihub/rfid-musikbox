import json
from pathlib import Path
from filelock import FileLock


class MappingStorage:
    """Verwaltet die Zuordnung UID -> Ordnername in einer JSON-Datei."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.lock_path = str(self.file_path) + ".lock"
        # Ordner anlegen, falls er noch nicht existiert
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        # Datei anlegen, falls sie noch nicht existiert
        if not self.file_path.exists():
            self._write({})

    def _read(self) -> dict:
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_folder_for_uid(self, uid: str) -> str | None:
        """Gibt den zugeordneten Ordnernamen zurück, oder None falls unbekannt."""
        data = self._read()
        return data.get(uid)

    def set_mapping(self, uid: str, folder_name: str) -> None:
        """Legt eine neue Zuordnung an oder überschreibt eine bestehende."""
        with FileLock(self.lock_path):
            data = self._read()
            data[uid] = folder_name
            self._write(data)

    def delete_mapping(self, uid: str) -> None:
        """Entfernt eine Zuordnung, falls vorhanden."""
        with FileLock(self.lock_path):
            data = self._read()
            data.pop(uid, None)
            self._write(data)

    def list_mappings(self) -> dict:
        """Gibt alle Zuordnungen zurück (für die Übersicht im Web-Interface)."""
        return self._read()