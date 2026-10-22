import sqlite3
import unittest
from contextlib import closing, redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import imagehash
from PIL import Image

from tcg_card_recognizer import Recognizer


class RecognizerTests(unittest.TestCase):
    def test_bundled_database_contains_cards(self):
        recognizer = Recognizer()
        self.assertTrue(recognizer.db_path.is_file())
        self.assertTrue(recognizer._get_cards())
        with closing(recognizer._get_db()) as db, self.assertRaises(sqlite3.OperationalError):
            db.execute("CREATE TABLE should_not_be_created (id INTEGER)")

    def test_recognize_returns_ranked_matches_without_printing(self):
        image = Image.new("RGB", (200, 279), "red")
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        query_hash = int(str(imagehash.phash(image)), 16)

        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "cards.db"
            with closing(sqlite3.connect(db_path)) as db:
                db.executescript(
                    "CREATE TABLE card_set (group_id TEXT, abb TEXT);"
                    "CREATE TABLE card (id INTEGER, normalized_name TEXT, number TEXT, "
                    "phash TEXT, group_id TEXT);"
                    "INSERT INTO card_set VALUES ('1', 'TEST');"
                )
                db.executemany(
                    "INSERT INTO card VALUES (?, ?, ?, ?, '1')",
                    [
                        (1, "other", "002", f"{query_hash ^ 3:016x}"),
                        (2, "exact", "001", f"{query_hash:016x}"),
                    ],
                )
                db.commit()

            recognizer = Recognizer(str(db_path))
            output = StringIO()
            with redirect_stdout(output):
                matches = recognizer.recognize(image_bytes.getvalue())
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(
                matches,
                [(0, 2, "exact", "001", "TEST"), (2, 1, "other", "002", "TEST")],
            )
            self.assertEqual(recognizer.recognize(image_bytes.getvalue(), top_k=1), matches[:1])

    def test_missing_database_is_not_created(self):
        with TemporaryDirectory() as directory:
            db_path = Path(directory) / "missing.db"
            with self.assertRaises(sqlite3.OperationalError):
                Recognizer(db_path)._get_cards()
            self.assertFalse(db_path.exists())


if __name__ == "__main__":
    unittest.main()
