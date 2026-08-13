"""B50 image generator using Pillow."""

import os
import functools
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from datetime import datetime, timezone

# ── Layout constants ─────────────────────────────────────────────────────────
NUM_COLS     = 3
GRID_GAP     = 8     # pixels between cards, both directions
GRID_MARGIN  = 10    # outer margin around the whole card grid
CARD_WIDTH   = 320
CARD_HEIGHT  = 72
NUM_ROWS     = 17    # ceil(50 / 3); row 0 = metadata + cards 49-50, rows 1-16 = cards 1-48
IMAGE_WIDTH  = GRID_MARGIN * 2 + CARD_WIDTH * NUM_COLS + GRID_GAP * (NUM_COLS - 1)   # 996
IMAGE_HEIGHT = GRID_MARGIN * 2 + CARD_HEIGHT * NUM_ROWS + GRID_GAP * (NUM_ROWS - 1)  # 1372

JACKET_SIZE = CARD_HEIGHT  # jacket fills the full height of the card
JACKET_PAD  = 0             # flush against the card's left edge
INFO_MARGIN = 8             # gap between jacket right edge and text
INFO_X_OFF  = JACKET_PAD + JACKET_SIZE + INFO_MARGIN

# ── Colours ──────────────────────────────────────────────────────────────────
WHITE     = (238, 240, 236)
GRAY      = (135, 145, 135)
GOLD      = (242, 242, 242)

# Per-mode colour schemes: "nabla" (current game) vs "exceed" (Exceed Gear, the
# previous version). Selected at render time via data["mode"].
COLOR_SCHEMES = {
    "nabla": {
        "bg_top":    (3, 16, 7),      # near-black green, top-left
        "bg_bottom": (11, 63, 18),    # rich, saturated green, bottom-right
        "card_tint": (190, 255, 200), # soft mint-green card highlight
        "label":     "NABLA VF B50",
    },
    "exceed": {
        "bg_top":    (12, 13, 15),    # near-black gray, top-left
        "bg_bottom": (58, 60, 65),    # lighter slate gray, bottom-right
        "card_tint": (225, 228, 232), # soft cool-white card highlight
        "label":     "EXCEED GEAR VF B50",
    },
}

DIFF_STYLES = {
    # bg = rgba blended onto card avg (16,22,16); text = css color literal
    "NOV": {"text": (255, 102, 255), "bg": ( 75,  17,  75)},
    "ADV": {"text": (255, 208, 102), "bg": ( 75,  67,  32)},
    "EXH": {"text": (255, 136, 136), "bg": ( 75,  42,  42)},
    "MXM": {"text": (208, 208, 208), "bg": ( 52,  57,  52)},
    "INF": {"text": (200, 140, 255), "bg": ( 57,  42,  76)},
    "GRV": {"text": (255, 174, 102), "bg": ( 75,  52,  27)},
    "HVN": {"text": (136, 232, 255), "bg": ( 32,  72,  76)},
    "VVD": {"text": (255, 154, 200), "bg": ( 75,  47,  57)},
    "XCD": {"text": (136, 184, 255), "bg": ( 32,  52,  76)},
    "ULT": {"text": (255, 240, 153), "bg": ( 75,  77,  42)},
}

LAMP_SHORT = {
    "PERFECT ULTIMATE CHAIN": "PUC",
    "ULTIMATE CHAIN":         "UC",
    "MAXXIVE CLEAR":          "MXV",
    "EXCESSIVE CLEAR":        "EXC",
    "CLEAR":                  "CLR",
    "FAILED":                 "FAIL",
}

LAMP_STYLES = {
    "PUC":  {"text": ( 60,  40,   0), "bg": (220, 180,  40)},
    "UC":   {"text": (255, 255, 255), "bg": (210,  80, 140)},
    "MXV":  {"text": ( 30,  30,  30), "bg": (180, 185, 180)},
    "EXC":  {"text": (255, 255, 255), "bg": (210, 110,  30)},
    "CLR":  {"text": (255, 255, 255), "bg": ( 60, 120, 210)},
    "FAIL": {"text": (255, 255, 255), "bg": (180,  45,  45)},
}

JACKET_BASE_URL = "https://sdvx.dev/api/cover"
_DIR            = os.path.dirname(os.path.abspath(__file__))
JACKET_CACHE    = os.path.join(_DIR, ".jacket_cache")
os.makedirs(JACKET_CACHE, exist_ok=True)


# ── Font helpers ─────────────────────────────────────────────────────────────

_POPPINS = os.path.join(_DIR, "asset", "Poppins-Medium.ttf")

_IBM_PLEX_JP = os.path.join(_DIR, "asset", "IBMPlexSansJP-Medium.ttf")

_NOTO_SANS = os.path.join(_DIR, "asset", "NOTOSANS-REGULAR.TTF")

_CJK_CANDIDATES = [
    (_IBM_PLEX_JP,                                              None),
    (_NOTO_SANS,                                              None),
]


@functools.lru_cache(maxsize=64)
def font(size):
    if os.path.exists(_POPPINS):
        try:
            return ImageFont.truetype(_POPPINS, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


@functools.lru_cache(maxsize=64)
def _cjk_font(size):
    for path, idx in _CJK_CANDIDATES:
        if os.path.exists(path):
            try:
                kw = {"index": idx} if idx is not None else {}
                return ImageFont.truetype(path, size, **kw)
            except Exception:
                pass
    return font(size)


def _needs_fallback(text):
    # anything beyond Latin Extended-B (U+024F) needs a fallback font
    return any(ord(ch) > 0x024F for ch in text)


def best_font(size, text):
    return _cjk_font(size) if _needs_fallback(text) else font(size)


# ── Jacket fetching ──────────────────────────────────────────────────────────

def _fetch_jacket(song_id):
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


def prefetch_jackets(start=1, end=3000, max_workers=4):
    """Warm the on-disk jacket cache for song ids in [start, end]."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        list(pool.map(_fetch_jacket, range(start, end + 1)))


# ── Utility functions ────────────────────────────────────────────────────────

def _score_parts(score):
    """Return (high, low) 4-char strings from an 8-digit zero-padded score."""
    s = f"{int(score or 0):08d}"
    return s[:4], s[4:]


def _time_ago(ts_ms):
    """Return 'x hours/days/months ago' from a Unix-millisecond timestamp."""
    if not ts_ms:
        return ""
    try:
        now  = datetime.now(timezone.utc)
        then = datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=timezone.utc)
        secs = max(0.0, (now - then).total_seconds())
        h = int(secs / 3600)
        d = int(secs / 86400)
        m = int(d / 30)
        if h < 24:
            return f"{h} hour{'s' if h != 1 else ''} ago"
        if d < 30:
            return f"{d} day{'s' if d != 1 else ''} ago"
        return f"{m} month{'s' if m != 1 else ''} ago"
    except Exception:
        return ""


def _truncate(draw, text, fnt, max_px):
    if not text:
        return ""
    try:
        if draw.textlength(text, font=fnt) <= max_px:
            return text
    except Exception:
        return text
    ellipsis = "…"
    while text:
        text = text[:-1]
        try:
            if draw.textlength(text + ellipsis, font=fnt) <= max_px:
                return text + ellipsis
        except Exception:
            break
    return text


def _background_gradient(width, height, bg_top, bg_bottom):
    """Diagonal (top-left → bottom-right) gradient used as the canvas backdrop."""
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    t  = (xs[None, :] + ys[:, None]) / 2.0  # 0 at top-left, 1 at bottom-right

    top    = np.array(bg_top, dtype=np.float32)
    bottom = np.array(bg_bottom, dtype=np.float32)
    arr    = top[None, None, :] + (bottom - top)[None, None, :] * t[:, :, None]
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


@functools.lru_cache(maxsize=4)
def _card_gradient_overlay(tint):
    """Subtle tinted gradient, transparent at top fading in toward the bottom of a card."""
    start_frac = 0.2
    max_alpha  = 20
    grad = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    start_y = int(CARD_HEIGHT * start_frac)
    for y in range(start_y, CARD_HEIGHT):
        t     = (y - start_y) / max(1, (CARD_HEIGHT - 1 - start_y))
        alpha = int(max_alpha * t)
        gd.line([(0, y), (CARD_WIDTH, y)], fill=(*tint, alpha))
    return grad


# ── Card drawing ─────────────────────────────────────────────────────────────

def _draw_card(img, draw, score, cx, cy, rank, jcache, card_tint):
    # Jacket
    sid    = score.get("songId")
    jacket = None
    if sid:
        sid = str(sid)
        if sid not in jcache:
            jcache[sid] = _fetch_jacket(sid)
        jacket = jcache[sid]

    jx = cx + JACKET_PAD
    jy = cy + (CARD_HEIGHT - JACKET_SIZE) // 2

    if jacket:
        jacket = jacket.resize((JACKET_SIZE, JACKET_SIZE), Image.LANCZOS)
        jacket = ImageEnhance.Brightness(jacket).enhance(0.88)
        jacket = ImageEnhance.Contrast(jacket).enhance(0.92)
        img.paste(jacket, (jx, jy))
        draw.rectangle(
            [jx, jy, jx + JACKET_SIZE - 1, jy + JACKET_SIZE - 1],
            outline=(80, 90, 80),
            width=2,
        )
    else:
        draw.rectangle([jx, jy, jx + JACKET_SIZE - 1, jy + JACKET_SIZE - 1], fill=(22, 24, 38))
        draw.text(
            (jx + JACKET_SIZE // 2, jy + JACKET_SIZE // 2),
            "♪",
            font=font(18),
            fill=(50, 55, 80),
            anchor="mm",
        )

    # Info area
    ix    = cx + INFO_X_OFF
    max_w = (cx + CARD_WIDTH) - ix - 4

    f_badge = font(10)
    f_score = font(17)

    # 1. Title — use CJK fallback if Poppins lacks any glyph
    raw_title = score.get("title", "")
    f_title   = best_font(17, raw_title)
    title     = _truncate(draw, raw_title, f_title, max_w)
    draw.text((ix, cy + 4), title, font=f_title, fill=WHITE)

    # 2. Badge row: diff | lamp | vf
    diff       = (score.get("diff") or "EXH").upper()
    level      = f"{float(score.get("level", "")):.1f}"
    diff_style = DIFF_STYLES.get(diff, DIFF_STYLES["EXH"])
    diff_label = f"{diff} {level}"

    lamp_full  = (score.get("lamp") or "FAILED").upper()
    lamp_key   = LAMP_SHORT.get(lamp_full, lamp_full[:4])
    lamp_style = LAMP_STYLES.get(lamp_key, LAMP_STYLES["FAIL"])

    raw_vf   = score.get("vf")
    vf_label = f"{float(raw_vf):.3f}" if raw_vf is not None else "-.---"

    BADGE_H  = 14
    BADGE_PAD_X = 5
    bx = ix
    by = cy + 29
    for label, fg, bg in [
        (diff_label, diff_style["text"], diff_style["bg"]),
        (lamp_key,   lamp_style["text"], lamp_style["bg"]),
        (vf_label,   (220, 220, 220),    (40, 60, 40)),
    ]:
        try:
            bw = int(draw.textlength(label, font=f_badge)) + BADGE_PAD_X * 2
        except Exception:
            bw = len(label) * 6 + BADGE_PAD_X * 2
        draw.rounded_rectangle([bx, by, bx + bw, by + BADGE_H],radius=2, fill=bg)
        draw.text((bx + BADGE_PAD_X, by), label, font=f_badge, fill=fg)
        bx += bw + 3

    # 3. Score (left) · timestamp · #rank (right) — all one row
    f_small   = font(15)
    right_x   = cx + CARD_WIDTH - 4
    score_y   = cy + 45
    small_y   = cy + 47   # vertically centered in the score text area

    high, low   = _score_parts(score.get("score", 0))
    f_score_sm  = font(12)
    draw.text((ix, score_y), high, font=f_score, fill=(245, 245, 245))
    try:
        big_bb = draw.textbbox((ix, score_y), high, font=f_score)
        sm_bb  = draw.textbbox((0, 0), low, font=f_score_sm)
        sm_x   = big_bb[2] + 1
        sm_y   = big_bb[3] - (sm_bb[3] - sm_bb[1]) - 4
    except Exception:
        sm_x = ix + len(high) * 10
        sm_y = score_y + 5
    draw.text((sm_x, sm_y), low, font=f_score_sm, fill=(190, 190, 190))

    rank_text = f"#{rank}"
    draw.text((right_x, small_y), rank_text, font=f_small, fill=GRAY, anchor="ra")

    ta = _time_ago(score.get("timeAchieved"))
    if ta:
        try:
            rank_w = int(draw.textlength(rank_text, font=f_small)) + 6
        except Exception:
            rank_w = 20
        draw.text((right_x - rank_w, small_y + 5), ta, font=font(10), fill=GRAY, anchor="ra")

    # Slight tinted gradient wash across the bottom of the card
    overlay = _card_gradient_overlay(card_tint)
    img.paste(overlay, (cx, cy), overlay)


# ── Public entry point ───────────────────────────────────────────────────────

def generate_b50_image(data: dict) -> Image.Image:
    """
    Build the B50 card image and return a PIL Image.

    Expected keys in *data*:
        username   str
        vf         float
        mode       str  – "nabla" (default) or "exceed" (Exceed Gear), picks the colour scheme
        scores     list[dict]  – up to 50 items, each with:
                       title, diff, level, score, grade, lamp, vf,
                       songId, timeAchieved (ms)
    """
    scores   = (data.get("scores") or [])[:50]
    username = data.get("username") or "Player"
    vf       = float(data.get("vf") or 0)
    now      = datetime.now(timezone.utc)

    mode   = (data.get("mode") or "nabla").lower()
    scheme = COLOR_SCHEMES.get(mode, COLOR_SCHEMES["nabla"])

    img  = _background_gradient(IMAGE_WIDTH, IMAGE_HEIGHT, scheme["bg_top"], scheme["bg_bottom"])
    draw = ImageDraw.Draw(img)

    def _slot_xy(col, row):
        return (
            GRID_MARGIN + col * (CARD_WIDTH + GRID_GAP),
            GRID_MARGIN + row * (CARD_HEIGHT + GRID_GAP),
        )

    # ── Metadata block (top-left card slot: col 0, row 0) ────────────────────
    mx, my = _slot_xy(0, 0)
    draw.text((mx + 8,  my + 4), scheme["label"],            font=font(13),                   fill=(235, 235, 235))
    draw.text((mx + 8, my + 22), username,                    font=best_font(16, username),    fill=WHITE)
    draw.text((mx + 8, my + 45), f"{vf:.3f} VF",              font=font(17),                   fill=(255, 220, 90))
    draw.text((mx + CARD_WIDTH - 8,  my + 4), "whiteou7.github.io/new-vf-calc", font=font(9), fill=GRAY, anchor="ra")
    draw.text((mx + CARD_WIDTH - 8, my + 53), now.strftime("%B %d, %Y"),         font=font(9), fill=GRAY, anchor="ra")

    # ── Prefetch all jackets in parallel ─────────────────────────────────────
    song_ids = list({str(s["songId"]) for s in scores if s.get("songId")})
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(_fetch_jacket, sid): sid for sid in song_ids}
        jcache = {sid: f.result() for f, sid in ((f, futures[f]) for f in futures)}

    # ── Cards ────────────────────────────────────────────────────────────────
    # cards 49-50 (i=48,49) → row 0, cols 1-2
    # cards  1-48 (i= 0-47) → rows 1-16, cols 0-2
    for i, score in enumerate(scores):
        slot = i + 1  # slot 0 is the metadata block
        col  = slot % NUM_COLS
        row  = slot // NUM_COLS
        cx, cy = _slot_xy(col, row)
        _draw_card(
            img, draw, score,
            cx=cx, cy=cy,
            rank=i + 1,
            jcache=jcache,
            card_tint=scheme["card_tint"],
        )

    return img
