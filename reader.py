from abc import ABC, abstractmethod


class RFIDReader(ABC):
    """Abstraktes Interface, das jede Reader-Implementierung erfüllen muss."""

    @abstractmethod
    def read_uid(self) -> str | None:
        """Gibt die UID der aktuell aufgelegten Karte zurück, oder None wenn keine da ist."""
        raise NotImplementedError


class MFRC522Reader(RFIDReader):
    """Echte Implementierung, spricht über SPI mit dem RC522-Modul."""

    def __init__(self):
        # Import erst hier drin, nicht oben im Modul-Kopf:
        # mfrc522/SPI-Bibliotheken existieren nur auf dem Pi, nicht auf Windows.
        # So bleibt reader.py auch auf Windows importierbar (für FakeReader-Tests),
        # solange man MFRC522Reader nicht tatsächlich instanziiert.
        from mfrc522 import SimpleMFRC522
        self.reader = SimpleMFRC522()

    def read_uid(self) -> str | None:
        # read_no_block() gibt (None, None) zurück, wenn keine Karte da ist,
        # statt zu blockieren, bis eine aufgelegt wird.
        uid, _text = self.reader.read_no_block()
        return str(uid) if uid is not None else None


class FakeReader(RFIDReader):
    """Test-Implementierung: UID wird manuell über die Konsole gesetzt, für Tests ohne Hardware."""

    def __init__(self):
        self.current_uid: str | None = None

    def simulate_card_present(self, uid: str) -> None:
        """Testhilfsfunktion: simuliert, dass eine Karte aufgelegt wurde."""
        self.current_uid = uid

    def simulate_card_removed(self) -> None:
        """Testhilfsfunktion: simuliert, dass die Karte weggenommen wurde."""
        self.current_uid = None

    def read_uid(self) -> str | None:
        return self.current_uid