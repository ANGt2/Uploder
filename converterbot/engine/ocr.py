import subprocess
import tempfile
import os
from PIL import Image, ImageEnhance, ImageOps
import io
import re


def _fix_fa_spacing(text: str) -> str:
    fixes = {
        "نتهمراه": "نت همراه",
        "اینترنتهمراه": "اینترنت همراه",
        "سرورهایی": "سرور هایی",
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    return text


def _score_fa(text: str) -> int:
    fa_chars = re.findall(r"[\u0600-\u06FF]", text or "")
    lines = [l for l in (text or "").splitlines() if l.strip()]
    return len(fa_chars) + 3 * len(lines)


def _run_tesseract(img_path: str, lang: str, psm: int) -> str:
    cmd = [
        "tesseract",
        img_path,
        "stdout",
        "-l", lang,
        "--oem", "1",
        "--psm", str(psm),
        "-c", "preserve_interword_spaces=1",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return (res.stdout or "").strip()


def _preprocess(img_bytes: bytes) -> str:
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    w, h = im.size
    im = im.resize((w * 2, h * 2), Image.LANCZOS)

    im = ImageOps.grayscale(im)
    im = ImageEnhance.Contrast(im).enhance(2.2)

    # binarize
    im = im.point(lambda p: 255 if p > 170 else 0)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp_path = tmp.name
    tmp.close()
    im.save(tmp_path, format="PNG")
    return tmp_path


def image_bytes_to_text(img_bytes: bytes) -> str:
    processed_path = None
    try:
        processed_path = _preprocess(img_bytes)

        candidates = []
        for lang in ["fas", "fas+eng"]:
            for psm in [6, 11, 4]:
                out = _run_tesseract(processed_path, lang=lang, psm=psm)
                if out:
                    candidates.append(out)

        if not candidates:
            return ""

        best = max(candidates, key=_score_fa)
        best = _fix_fa_spacing(best)
        return best.strip()

    finally:
        if processed_path and os.path.exists(processed_path):
            try:
                os.remove(processed_path)
            except:
                pass
