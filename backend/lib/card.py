from PIL import Image, ImageEnhance

from .background import card_gradient_overlay
from .config import (
    CARD_HEIGHT, CARD_WIDTH, DIFF_STYLES, GRAY, INFO_X_OFF, JACKET_PAD,
    JACKET_SIZE, LAMP_SHORT, LAMP_STYLES, WHITE,
)
from .fonts import best_font, font
from .jackets import fetch_jacket
from .utils import score_parts, time_ago, truncate


def _draw_jacket(img, draw, jacket, jx, jy):
    box = [jx, jy, jx + JACKET_SIZE - 1, jy + JACKET_SIZE - 1]
    if jacket:
        jacket = jacket.resize((JACKET_SIZE, JACKET_SIZE), Image.LANCZOS)
        jacket = ImageEnhance.Brightness(jacket).enhance(0.88)
        jacket = ImageEnhance.Contrast(jacket).enhance(0.92)
        img.paste(jacket, (jx, jy))
        draw.rectangle(box, outline=(80, 90, 80), width=2)
    else:
        draw.rectangle(box, fill=(22, 24, 38))
        draw.text(
            (jx + JACKET_SIZE // 2, jy + JACKET_SIZE // 2),
            "♪",
            font=font(18),
            fill=(50, 55, 80),
            anchor="mm",
        )


def _draw_badges(draw, ix, cy, score):
    f_badge = font(10)

    diff       = (score.get("diff") or "EXH").upper()
    level      = f"{float(score.get('level', '')):.1f}"
    diff_style = DIFF_STYLES.get(diff, DIFF_STYLES["EXH"])
    diff_label = f"{diff} {level}"

    lamp_full  = (score.get("lamp") or "FAILED").upper()
    lamp_key   = LAMP_SHORT.get(lamp_full, lamp_full[:4])
    lamp_style = LAMP_STYLES.get(lamp_key, LAMP_STYLES["FAIL"])

    raw_vf   = score.get("vf")
    vf_label = f"{float(raw_vf):.3f}" if raw_vf is not None else "-.---"

    badge_h     = 14
    badge_pad_x = 5
    bx = ix
    by = cy + 29
    for label, fg, bg in [
        (diff_label, diff_style["text"], diff_style["bg"]),
        (lamp_key,   lamp_style["text"], lamp_style["bg"]),
        (vf_label,   (220, 220, 220),    (40, 60, 40)),
    ]:
        try:
            bw = int(draw.textlength(label, font=f_badge)) + badge_pad_x * 2
        except Exception:
            bw = len(label) * 6 + badge_pad_x * 2
        draw.rounded_rectangle([bx, by, bx + bw, by + badge_h], radius=2, fill=bg)
        draw.text((bx + badge_pad_x, by), label, font=f_badge, fill=fg)
        bx += bw + 3


def _draw_score_row(draw, score, ix, cx, cy, rank):
    """Score (left), timestamp and #rank (right), all one row."""
    f_score    = font(17)
    f_score_sm = font(12)
    f_small    = font(15)
    right_x    = cx + CARD_WIDTH - 4
    score_y    = cy + 45
    small_y    = cy + 47

    high, low = score_parts(score.get("score", 0))
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

    ago = time_ago(score.get("timeAchieved"))
    if ago:
        try:
            rank_w = int(draw.textlength(rank_text, font=f_small)) + 6
        except Exception:
            rank_w = 20
        draw.text((right_x - rank_w, small_y + 5), ago, font=font(10), fill=GRAY, anchor="ra")


def draw_card(img, draw, score, cx, cy, rank, jcache, card_tint):
    sid    = score.get("songId")
    jacket = None
    if sid:
        sid = str(sid)
        if sid not in jcache:
            jcache[sid] = fetch_jacket(sid)
        jacket = jcache[sid]

    _draw_jacket(img, draw, jacket, cx + JACKET_PAD, cy + (CARD_HEIGHT - JACKET_SIZE) // 2)

    ix    = cx + INFO_X_OFF
    max_w = (cx + CARD_WIDTH) - ix - 4

    raw_title = score.get("title", "")
    f_title   = best_font(17, raw_title)
    draw.text((ix, cy + 4), truncate(draw, raw_title, f_title, max_w), font=f_title, fill=WHITE)

    _draw_badges(draw, ix, cy, score)
    _draw_score_row(draw, score, ix, cx, cy, rank)

    overlay = card_gradient_overlay(card_tint)
    img.paste(overlay, (cx, cy), overlay)
