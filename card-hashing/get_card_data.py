import requests
import json
import sqlite3
import time
from pathlib import Path
from PIL import Image
import imagehash
from io import BytesIO
import random
from python_ntfy import NtfyClient

client = NtfyClient(server='')
db_path = Path(__file__).resolve().parent.parent / 'tcg-data.db'
db = sqlite3.connect(db_path)

session = requests.Session()
session.headers.update({'User-Agent': "TCG-Card-Recognizer/0.1"})
user_agents = [
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0",
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
         ]

def get_products(game_id,group_id):
    r = session.get(f"https://tcgcsv.com/tcgplayer/{game_id}/{group_id}/products", timeout=5)
    r.raise_for_status()
    products = r.json()['results']
    failed = 0
    for product in products:
        if product['extendedData'][0]['name'] == 'Number':
            number = next(
                    (
                        field['value']
                        for field in (product.get('extendedData') or [])
                        if field.get('name') == 'Number'
                        ),
                    None,
                    )
            if number is None:
                continue
            number = number.split('/')[0]
            for attempt in range(5):
                    try:
                        img_url  = product['imageUrl']
                        img = requests.get(img_url, timeout=5, headers={'User-Agent': random.choice(user_agents)})
                        img.raise_for_status()
                        with Image.open(BytesIO(img.content)) as image:
                            phash = str(imagehash.phash(image.convert('RGB')))
                        
                        db.execute("INSERT OR IGNORE INTO card (product_id, name, normalized_name, number, group_id, phash) VALUES (?,?,?,?,?,?)",
                                  (product['productId'], product['name'], product['cleanName'], number, group_id, phash))
                        db.commit()
                        print(f"Inserted {product['name']}")
                        failed = 0
                        time.sleep(1)
                        break
                    except Exception as e:
                        if attempt == 4:
                            client.send(f"Failed to insert {product['name']}")
                        failed += 1
                        if failed > 5 and failed < 10:
                            client.send(f"Last 5 items failed | %s", str(e))
                        time.sleep(10)
                        if failed > 10:
                            client.send('Terminating')
                            raise Exception('Terminating')
                        continue

def get_groups():
    games_ids = get_games()
    for game_id in games_ids:
        r = session.get(f"https://tcgcsv.com/tcgplayer/{game_id}/groups")
        all_groups = r.json()['results']
        for group in all_groups:
            db.execute("INSERT OR IGNORE INTO card_set (group_id, category_id, name, abb) VALUES (?,?,?,?)",
                       (group['groupId'], game_id, group['name'], group['abbreviation']))
            db.commit()
            get_products(game_id,group['groupId'])
        time.sleep(5)
    pass

def get_games() -> tuple:
    games = db.execute("SELECT category_id FROM game").fetchall()
    game_ids = (game[0] for game in games)
    return game_ids

get_groups()
