from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os
import re

import arabic_reshaper
from bidi.algorithm import get_display

# --- Fonts ---
FA_FONT_NAME = "Vazirmatn"
FA_FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "fonts", "Vazirmatn-Regular.ttf")

# مسیر DejaVu روی Termux معمولاً یکی از این‌هاست:
CANDIDATE_DV = [
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
DV_FONT_PATH = next((p for p in CANDIDATE_DV if os.path.exists(p)), None)
DV_FONT_NAME = "DejaVuSans"

pdfmetrics.registerFont(TTFont(FA_FONT_NAME, FA_FONT_PATH))
if DV_FONT_PATH:
    pdfmetrics.registerFont(TTFont(DV_FONT_NAME, DV_FONT_PATH))

# تشخیص اینکه خط فارسی/عربی دارد یا نه
ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")

def shape_fa(line: str) -> str:
    # shaping + bidi برای فارسی/عربی
    reshaped = arabic_reshaper.reshape(line)
    return get_display(reshaped)

def text_to_pdf(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        c = canvas.Canvas(f.name, pagesize=A4)
        width, height = A4

        x_margin = 40
        y = height - 40
        line_h = 18

        for raw in text.splitlines():
            if y < 40:
                c.showPage()
                y = height - 40

            is_fa = bool(ARABIC_RE.search(raw))

            if is_fa:
                c.setFont(FA_FONT_NAME, 12)
                line = shape_fa(raw)
                c.drawRightString(width - x_margin, y, line)
            else:
                # روسی/انگلیسی (اگر DejaVu نبود، همان Vazirmatn را می‌گذارد)
                c.setFont(DV_FONT_NAME if DV_FONT_PATH else FA_FONT_NAME, 12)
                c.drawString(x_margin, y, raw)

            y -= line_h

        c.save()
        f.seek(0)
        return f.read()
