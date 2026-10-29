import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR   = os.path.join(BACKEND_DIR, "asset")

NUM_COLS     = 3
GRID_GAP     = 8
GRID_MARGIN  = 10
CARD_WIDTH   = 320
CARD_HEIGHT  = 72
NUM_ROWS     = 17  # row 0 = metadata + cards 49-50, rows 1-16 = cards 1-48
IMAGE_WIDTH  = GRID_MARGIN * 2 + CARD_WIDTH * NUM_COLS + GRID_GAP * (NUM_COLS - 1)
IMAGE_HEIGHT = GRID_MARGIN * 2 + CARD_HEIGHT * NUM_ROWS + GRID_GAP * (NUM_ROWS - 1)

JACKET_SIZE = CARD_HEIGHT
JACKET_PAD  = 0
INFO_MARGIN = 8
INFO_X_OFF  = JACKET_PAD + JACKET_SIZE + INFO_MARGIN

WHITE = (238, 240, 236)
GRAY  = (135, 145, 135)
GOLD  = (242, 242, 242)

COLOR_SCHEMES = {
    "nabla": {
        "bg_top":    (3, 16, 7),
        "bg_bottom": (11, 30, 18),
        "card_tint": (190, 255, 200),
        "art":       "jk_dummy_b_nbl.png",
        "label":     "NABLA VF B50",
    },
    "exceed": {
        "bg_top":    (12, 13, 15),
        "bg_bottom": (29, 30, 32),
        "card_tint": (225, 228, 232),
        "art":       "jk_dummy_b_eg.png",
        "label":     "EXCEED GEAR VF B50",
    },
}

# bg = rgba blended onto card avg (16,22,16)
DIFF_STYLES = {
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
JACKET_CACHE    = os.path.join(BACKEND_DIR, ".jacket_cache")
