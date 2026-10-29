import functools
import os

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from .config import ASSET_DIR, CARD_HEIGHT, CARD_WIDTH


def background_gradient(width, height, bg_top, bg_bottom):
    """Diagonal (top-left -> bottom-right) gradient used as the canvas backdrop."""
    xs = np.linspace(0.0, 1.0, width, dtype=np.float32)
    ys = np.linspace(0.0, 1.0, height, dtype=np.float32)
    t  = (xs[None, :] + ys[:, None]) / 2.0

    top    = np.array(bg_top, dtype=np.float32)
    bottom = np.array(bg_bottom, dtype=np.float32)
    arr    = top[None, None, :] + (bottom - top)[None, None, :] * t[:, :, None]
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


@functools.lru_cache(maxsize=2)
def _bg_art_alpha(name, width, height):
    try:
        src = Image.open(os.path.join(ASSET_DIR, name)).convert("L")
    except OSError:
        return None

    canvas = ImageOps.fit(src, (width, height), Image.LANCZOS).filter(ImageFilter.GaussianBlur(9))

    art_h = round(src.height * width / src.width)
    top   = (height - art_h) // 2
    sharp = Image.new("L", (width, height), 0)
    sharp.paste(src.resize((width, art_h), Image.LANCZOS), (0, top))
    mask  = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rectangle([0, top, width, top + art_h - 1], fill=255)
    canvas = Image.composite(sharp, canvas, mask.filter(ImageFilter.GaussianBlur(20)))

    # dim it so card text stays legible; gamma 0.6 keeps the faint grid visible
    return canvas.point([round(97 * (v / 255) ** 0.6) for v in range(256)])


def apply_background_art(img, name):
    alpha = _bg_art_alpha(name, img.width, img.height)
    if alpha is None:
        return img
    return Image.composite(ImageEnhance.Brightness(img).enhance(6), img, alpha)


@functools.lru_cache(maxsize=4)
def card_gradient_overlay(tint):
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
