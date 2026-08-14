from engine.image import image_bytes_to_pdf
from engine.text import text_to_pdf
from engine.ocr import image_bytes_to_text

import telebot
from telebot import types

TOKEN = "8529661266:AAFJovoOAfHd-aeV1eoysZK9sW24KQWJIvg"

bot = telebot.TeleBot(TOKEN)

# ذخیره موقت file_id عکس‌ها برای اینکه callback_data کوتاه بماند
photo_cache = {}


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "🤖 ربات تبدیل فایل فعال شد.\n"
        "متن بفرست → PDF\n"
        "عکس بفرست → انتخاب OCR یا PDF\n"
        "فایل بفرست → فعلاً فقط دریافت می‌کنم."
    )


@bot.message_handler(content_types=["text", "photo", "document"])
def handle_all(message):
    try:
        # جلوگیری از تبدیل دستورها مثل /start به PDF
        if message.content_type == "text" and message.text and message.text.startswith("/"):
            return

        # متن → PDF
        if message.content_type == "text":
            pdf_bytes = text_to_pdf(message.text)
            bot.send_document(
                message.chat.id,
                pdf_bytes,
                visible_file_name="text.pdf"
            )
            return

        # عکس (Photo) → منوی انتخاب OCR/PDF
        if message.content_type == "photo":
            bot.send_message(message.chat.id, "✅ عکس دریافت شد. چی کار کنم؟")

            file_id = message.photo[-1].file_id

            # کلید کوتاه و امن برای callback_data
            key = f"{message.chat.id}:{message.message_id}"
            photo_cache[key] = file_id

            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🧠 استخراج متن (OCR)", callback_data=f"ocr|{key}"),
                types.InlineKeyboardButton("📄 تبدیل به PDF", callback_data=f"pdf|{key}")
            )

            bot.send_message(
                message.chat.id,
                "یک گزینه را انتخاب کن:",
                reply_markup=kb
            )
            return

        # فایل
        if message.content_type == "document":
            bot.reply_to(message, "📄 فایل دریافت شد")
            return

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در handle_all:\n{e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith(("ocr|", "pdf|")))
def handle_photo_action(call):
    try:
        action, key = call.data.split("|", 1)
        bot.answer_callback_query(call.id)

        file_id = photo_cache.get(key)
        if not file_id:
            bot.send_message(call.message.chat.id, "❌ این درخواست منقضی شده. لطفاً دوباره عکس بفرست.")
            return

        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)

        if action == "ocr":
            text = image_bytes_to_text(downloaded)
            if not text.strip():
                bot.send_message(call.message.chat.id, "❌ متنی پیدا نشد.")
            else:
                bot.send_message(call.message.chat.id, f"🧠 متن استخراج‌شده:\n\n{text[:3500]}")
            return

        if action == "pdf":
            pdf_bytes = image_bytes_to_pdf(downloaded)
            bot.send_document(call.message.chat.id, pdf_bytes, visible_file_name="image.pdf")
            return

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطا در دکمه‌ها:\n{e}")


print("ConverterBot is running...")
bot.infinity_polling()
