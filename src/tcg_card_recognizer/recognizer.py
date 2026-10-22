import sqlite3
from contextlib import closing
from io import BytesIO
from pathlib import Path

import imagehash
from PIL import Image


class Recognizer:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = (
            Path(db_path) if db_path is not None else Path(__file__).parent / "tcg-data.db"
        )

    def _get_db(self) -> sqlite3.Connection:
        return sqlite3.connect(f"{self.db_path.resolve().as_uri()}?mode=ro", uri=True)

    def _get_cards(self):
        with closing(self._get_db()) as db:
            rows = db.execute(
                "SELECT c.id, c.normalized_name,c.number, c.phash, cs.abb from card c "
                "LEFT JOIN card_set cs ON c.group_id = cs.group_id"
            )

            return [(row[0], row[1], row[2], int(row[3], 16), row[4]) for row in rows]

    def recognize(self, image: bytes, top_k: int = 5):
        """Return (distance, card_id, name, number, set_abbreviation) matches."""
        with Image.open(BytesIO(image)) as img:
            cards = self._get_cards()
            img = img.resize((200, 279))
            query = int(str(imagehash.phash(img.convert("RGB"))), 16)
            return self.find_closest(query, cards, top_k)

    def find_closest(self, query_hash: int, hashes: list, top_k: int = 5):
        results = []

        for card_id, name, number, stored_hash, abb in hashes:
            distance = (query_hash ^ stored_hash).bit_count()

            results.append((distance, card_id, name, number, abb))

        return sorted(results)[:top_k]
