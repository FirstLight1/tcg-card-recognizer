import os
import random
import sqlite3
import time
import unicodedata
from io import BytesIO
from pathlib import Path

import dotenv
import imagehash
import requests
from PIL import Image
from python_ntfy import NtfyClient

dotenv.load_dotenv()
topic = os.getenv('NOTIFICATION_TOPIC')
client = NtfyClient(topic=topic)
db_path = Path(__file__).resolve().parent.parent / 'tcg-data.db'
db = sqlite3.connect(db_path)

session = requests.Session()
session.headers.update({'User-Agent': "TCG-Card-Recognizer/0.1"})
user_agents = [
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0",
         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
         ]

def notify(message):
    try:
        client.send(message)
    except Exception as error:
        print(f"Notification failed: {error}")

def normalize(s: str | None) -> str | None:
    if s is None:
        return None
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower()


def get_products(game_id,group_id):
    r = session.get(f"https://tcgcsv.com/tcgplayer/{game_id}/{group_id}/products", timeout=5)
    r.raise_for_status()
    products = r.json()['results']
    for product in products:
        number = next(
            (field.get('value') for field in (product.get('extendedData') or [])
             if field.get('name') == 'Number'),
            None,
        )
        if not isinstance(number, str) or not number.strip():
            continue
        number = number.split('/')[0].strip()
        phash = None
        for attempt in range(5):
            try:
                img_url = product['imageUrl']
                with requests.get(img_url, timeout=5, headers={'User-Agent': random.choice(user_agents)}) as img:
                    img.raise_for_status()
                    with Image.open(BytesIO(img.content)) as image:
                        phash = str(imagehash.phash(image.convert('RGB')))
                break
            except (requests.RequestException, OSError, ValueError) as error:
                if isinstance(error, requests.HTTPError) and error.response is not None:
                    status = error.response.status_code
                    if status in (403, 404):
                        print(f"Skipped {product['name']} ({product['productId']}): image unavailable (HTTP {status}): {img_url}")
                        break
                if attempt < 4:
                    time.sleep(3)
                else:
                    notify(f"Failed to process {product['name']} after 5 attempts: {error}")
        if phash is None:
            continue
        name = product['name'].split("-")[0].strip()
        cursor = db.execute(
            "INSERT OR IGNORE INTO card (product_id, name, normalized_name, number, group_id, phash) VALUES (?,?,?,?,?,?)",
            (product['productId'], product['name'], normalize(name),number, group_id, phash),
        )
        db.commit()
        if cursor.rowcount:
            print(f"Inserted {product['name']}")
        else:
            print(f"Skipped {product['name']} (insert ignored)")
        time.sleep(1)

def get_groups():
    start = time.time()
    games_ids = get_games()
    for game_id in games_ids:
        r = session.get(f"https://tcgcsv.com/tcgplayer/{game_id}/groups", timeout=5)
        r.raise_for_status()
        all_groups = r.json()['results']
        for group in all_groups:
        #FIX: sets were not saved
            db.execute("INSERT OR IGNORE INTO card_set (group_id, category_id, name, abb) VALUES (?,?,?,?)",
                       (group['groupId'], game_id, group['name'], group['abbreviation']))
            db.commit()
            print(f"Inserted {group['name']}")
            get_products(game_id,group['groupId'])
        time.sleep(5)
    finish = time.time() - start
    print(f"Finished in {finish:.2f} seconds")
    notify(f"Finished in {finish:.2f} seconds")
    

def get_games():
    games = db.execute("SELECT category_id FROM game").fetchall()
    game_ids = (game[0] for game in games)
    return game_ids

if __name__ == '__main__':
    get_groups()
    if False:
        get_products(3,24382)
        get_products(3,24448)
        get_products(3,24451)
        get_products(3,24461)
        get_products(3,24493)
        get_products(3,24529)
        get_products(3,24541)
        get_products(3,24584)
        get_products(3,24587)
        get_products(3,24655)
        get_products(3,24688)
        get_products(3,24722)
        get_products(3,24831)
        get_products(3,24837)
        get_products(3,24864)
