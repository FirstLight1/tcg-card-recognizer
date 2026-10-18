from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().parent.parent / 'tcg-data.db'
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
            group_id TEXT NOT NULL,
            category_id TEXT NOT NULL,
            name TEXT,
            abb TEXT,
            FOREIGN KEY(category_id) REFERENCES game(category_id)
            );
            """)

cur.execute("""
        CREATE TABLE IF NOT EXISTS card (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            name TEXT,
            normalized_name TEXT,
            number TEXT,
            group_id TEXT,
            phash blob,
            FOREIGN KEY(group_id) REFERENCES card_set(group_id)
            );
            """)

