import sys
from pathlib import Path

# Damit Python die Module aus dem Hauptordner findet (player.py, reader.py, etc.)
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon import run
from player import FakePlayer
from reader import FakeReader
from storage import MappingStorage


class LimitedFakeReader(FakeReader):
    """Reader, der sich nach N Abfragen selbst 'ausschaltet', damit die Endlosschleife stoppt."""

    def __init__(self, max_polls: int):
        super().__init__()
        self.max_polls = max_polls
        self.poll_count = 0

    def read_uid(self):
        self.poll_count += 1
        if self.poll_count > self.max_polls:
            raise StopIteration("Testlauf beendet")
        return super().read_uid()


def test_play_and_stop(tmp_path):
    # Testweise eigene mappings.json in einem temporären Ordner (pytest stellt tmp_path bereit)
    storage = MappingStorage(str(tmp_path / "mappings.json"))
    storage.set_mapping("1234567890", "beatles-abbey-road")

    player = FakePlayer()
    reader = LimitedFakeReader(max_polls=10)

    # Karte direkt zu Beginn auflegen
    reader.simulate_card_present("1234567890")

    try:
        run(reader, player, storage, poll_interval_seconds=0)
    except StopIteration:
        pass  # erwartetes Ende des Testlaufs

    assert player.current_folder == "beatles-abbey-road"