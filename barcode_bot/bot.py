"""
Simple Telegram Barcode Bot (Code128)
Replace BOT_TOKEN with your own token before running.
"""

import io
import logging

import barcode
from barcode.writer import ImageWriter
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = "8926848759:AAHd512EUYfhFO4Vfnd0Fb7w6shp1KhYy_c"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏷 Barcode Generator\n\n"
        "هر متن، عدد یا لینک را ارسال کن."
    )


def make_barcode(text: str):
    buf = io.BytesIO()
    code = barcode.get("code128", text, writer=ImageWriter())
    code.write(
        buf,
        {
            "module_width": 0.35,
            "module_height": 18,
            "font_size": 10,
            "text_distance": 4,
            "quiet_zone": 5,
            "dpi": 300,
        },
    )
    buf.seek(0)
    buf.name = "barcode.png"
    return buf


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if not text:
        return

    if len(text) > 100:
        await update.message.reply_text("❌ حداکثر 100 کاراکتر مجاز است.")
        return

    wait = await update.message.reply_text("⏳ در حال ساخت بارکد...")

    try:
        img = make_barcode(text)
        await update.message.reply_photo(
            photo=img,
            caption=f"✅ Barcode ساخته شد\n\n{text}",
        )
        await wait.delete()
    except Exception:
        logging.exception("barcode")
        await wait.edit_text("❌ خطا در ساخت بارکد.")


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        raise RuntimeError("Please replace YOUR_BOT_TOKEN")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_text)
    )

    print("Barcode Bot Started...")
    app.run_polling()


if __name__ == "__main__":
    main()
