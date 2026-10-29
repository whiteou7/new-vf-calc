import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
from PIL import Image

from .config import JACKET_BASE_URL, JACKET_CACHE

os.makedirs(JACKET_CACHE, exist_ok=True)


def fetch_jacket(song_id):
    sid   = str(song_id)
    cache = os.path.join(JACKET_CACHE, f"{sid}.webp")
    if os.path.exists(cache):
        try:
            return Image.open(cache).convert("RGB")
        except Exception:
            pass
    url = f"{JACKET_BASE_URL}/{sid}_novice.webp"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            with open(cache, "wb") as fh:
                fh.write(r.content)
            return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        pass
    return None


def fetch_jackets(song_ids, max_workers=16):
    song_ids = list(song_ids)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return dict(zip(song_ids, pool.map(fetch_jacket, song_ids)))


def prefetch_jackets(start=1, end=3000, max_workers=4):
    """Warm the on-disk jacket cache for song ids in [start, end]."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(fetch_jacket, range(start, end + 1)))
