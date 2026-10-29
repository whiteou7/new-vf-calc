import functools
import os

from PIL import ImageFont

from .config import ASSET_DIR

_POPPINS = os.path.join(ASSET_DIR, "Poppins-Medium.ttf")
_CJK_PATHS = [
    os.path.join(ASSET_DIR, "IBMPlexSansJP-Medium.ttf"),
    os.path.join(ASSET_DIR, "NOTOSANS-REGULAR.TTF"),
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
    for path in _CJK_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return font(size)


def _needs_fallback(text):
    # anything beyond Latin Extended-B (U+024F) needs a fallback font
    return any(ord(ch) > 0x024F for ch in text)


def best_font(size, text):
    return _cjk_font(size) if _needs_fallback(text) else font(size)
