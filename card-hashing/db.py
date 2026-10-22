import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "src" / "tcg_card_recognizer" / "tcg-data.db"
con = sqlite3.connect(db_path)

cur = con.cursor()

cur.execute("""PRAGMA foreign_keys = ON""")

cur.execute("""
        CREATE TABLE IF NOT EXISTS game (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL UNIQUE,
            name TEXT
            );
            """)

cur.execute("""
        CREATE TABLE IF NOT EXISTS card_set (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT NOT NULL UNIQUE,
            category_id TEXT NOT NULL,
            name TEXT,
            abb TEXT,
            FOREIGN KEY(category_id) REFERENCES game(category_id)
            );
            """)

cur.execute("""
        CREATE TABLE IF NOT EXISTS card (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL UNIQUE,
            name TEXT,
            normalized_name TEXT,
            number TEXT,
            group_id TEXT,
            phash blob,
            FOREIGN KEY(group_id) REFERENCES card_set(group_id)
            );
            """)

cur.execute("""
            INSERT INTO game (category_id, name) VALUES (3, 'pokemon');
            """)

cur.execute("""
            INSERT INTO game (category_id, name) VALUES (68, 'one piece');
            """)

cur.execute("""
            INSERT INTO game (category_id, name) VALUES (89, 'riftbound');
            """)
