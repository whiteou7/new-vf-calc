from datetime import datetime, timezone

from PIL import Image, ImageDraw

from .background import apply_background_art, background_gradient
from .card import draw_card
from .config import (
    CARD_HEIGHT, CARD_WIDTH, COLOR_SCHEMES, GRAY, GRID_GAP, GRID_MARGIN,
    IMAGE_HEIGHT, IMAGE_WIDTH, NUM_COLS, WHITE,
)
from .fonts import best_font, font
from .jackets import fetch_jackets


def _slot_xy(col, row):
    return (
        GRID_MARGIN + col * (CARD_WIDTH + GRID_GAP),
        GRID_MARGIN + row * (CARD_HEIGHT + GRID_GAP),
    )


def _draw_metadata(draw, scheme, username, vf, now):
    mx, my = _slot_xy(0, 0)
    draw.text((mx + 8,  my + 4), scheme["label"],           font=font(13),                fill=(235, 235, 235))
    draw.text((mx + 8, my + 22), username,                   font=best_font(16, username), fill=WHITE)
    draw.text((mx + 8, my + 45), f"{vf:.3f} VF",             font=font(17),                fill=(255, 220, 90))
    draw.text((mx + CARD_WIDTH - 8,  my + 4), "whiteou7.github.io/new-vf-calc", font=font(9), fill=GRAY, anchor="ra")
    draw.text((mx + CARD_WIDTH - 8, my + 53), now.strftime("%B %d, %Y"),        font=font(9), fill=GRAY, anchor="ra")


def generate_b50_image(data: dict) -> Image.Image:
    """
    Build the B50 card image and return a PIL Image.

    Expected keys in *data*:
        username   str
        vf         float
        mode       str  - "nabla" (default) or "exceed" (Exceed Gear), picks the colour scheme
        scores     list[dict]  - up to 50 items, each with:
                       title, diff, level, score, grade, lamp, vf,
                       songId, timeAchieved (ms)
    """
    scores   = (data.get("scores") or [])[:50]
    username = data.get("username") or "Player"
    vf       = float(data.get("vf") or 0)
    now      = datetime.now(timezone.utc)

    mode   = (data.get("mode") or "nabla").lower()
    scheme = COLOR_SCHEMES.get(mode, COLOR_SCHEMES["nabla"])

    img  = background_gradient(IMAGE_WIDTH, IMAGE_HEIGHT, scheme["bg_top"], scheme["bg_bottom"])
    img  = apply_background_art(img, scheme["art"])
    draw = ImageDraw.Draw(img)

    _draw_metadata(draw, scheme, username, vf, now)

    jcache = fetch_jackets({str(s["songId"]) for s in scores if s.get("songId")})

    # slot 0 is the metadata block, so card i sits in slot i + 1
    for i, score in enumerate(scores):
        slot = i + 1
        cx, cy = _slot_xy(slot % NUM_COLS, slot // NUM_COLS)
        draw_card(img, draw, score, cx, cy, i + 1, jcache, scheme["card_tint"])

    return img
