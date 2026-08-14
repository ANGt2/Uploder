from io import BytesIO
from PIL import Image

def image_bytes_to_pdf(image_bytes: bytes) -> BytesIO:
    img = Image.open(BytesIO(image_bytes))

    if img.mode != "RGB":
        img = img.convert("RGB")

    out = BytesIO()
    img.save(out, format="PDF")
    out.seek(0)
    out.name = "image.pdf"   # این خط مهمه

    return out
