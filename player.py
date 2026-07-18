from abc import ABC, abstractmethod
from mpd import MPDClient


class Player(ABC):
    """Abstraktes Interface, das jede Player-Implementierung erfüllen muss."""

    @abstractmethod
    def play_folder(self, folder_name: str) -> None:
        """Startet den angegebenen Ordner (= ein Album) von Track 1 an."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stoppt Wiedergabe komplett (kein Pause-Zustand)."""
        raise NotImplementedError


class MPDPlayer(Player):
    """Echte Implementierung, spricht mit dem laufenden MPD-Server."""

    def __init__(self, host: str = "localhost", port: int = 6600):
        self.client = MPDClient()
        self.client.connect(host, port)

    def play_folder(self, folder_name: str) -> None:
        self.client.clear()
        self.client.add(folder_name)
        self.client.play(0)

    def stop(self) -> None:
        self.client.stop()


class FakePlayer(Player):
    """Test-Implementierung ohne echtes MPD, für Logik-Tests auf Windows."""

    def __init__(self):
        self.current_folder: str | None = None

    def play_folder(self, folder_name: str) -> None:
        self.current_folder = folder_name
        print(f"[FakePlayer] Würde jetzt '{folder_name}' von Track 1 abspielen.")

    def stop(self) -> None:
        self.current_folder = None
        print("[FakePlayer] Gestoppt.")