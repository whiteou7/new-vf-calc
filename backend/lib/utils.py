from datetime import datetime, timezone


def score_parts(score):
    """Return (high, low) 4-char strings from an 8-digit zero-padded score."""
    s = f"{int(score or 0):08d}"
    return s[:4], s[4:]


def time_ago(ts_ms):
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


def truncate(draw, text, fnt, max_px):
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
