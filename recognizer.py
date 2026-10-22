import sqlite3
from io import BytesIO
from pathlib import Path

import imagehash
from PIL import Image

db_path = Path(__file__).resolve().parent / "tcg-data.db"


class Recognizer:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _get_cards(self):
        db = self._get_db()
        rows = db.execute(
            "SELECT c.id, c.normalized_name,c.number, c.phash, cs.abb from card c "
            "LEFT JOIN card_set cs ON c.group_id = cs.group_id"
        )

        return [(row[0], row[1], row[2], int(row[3], 16), row[4]) for row in rows]

    def recognize(self, image: bytes):
        with Image.open(BytesIO(image)) as img:
            cards = self._get_cards()
            img = img.resize((200, 279))
            query = int(str(imagehash.phash(img.convert("RGB"))), 16)
            closest = self.find_closest(query, cards)
            for distance, card_id, name, number, abb in closest:
                print(f"{name} - {number}, {abb}, {distance}")

    def find_closest(self, query_hash: int, hashes: list, top_k: int = 5):
        results = []

        for card_id, name, number, stored_hash, abb in hashes:
            distance = (query_hash ^ stored_hash).bit_count()

            results.append((distance, card_id, name, number, abb))

        return sorted(results)[:top_k]


if __name__ == "__main__":
    recognizer = Recognizer(db_path)
    recognizer.recognize(open("test.png", "rb").read())
