import os
import io
import sqlite3
import logging
import qrcode
import barcode
from barcode.writer import ImageWriter
from PIL import Image
from pyzbar.pyzbar import decode

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ----------------------------------------------------
# تنظیمات اصلی
# ----------------------------------------------------
BOT_TOKEN = "8672745569:AAHNR4jpbBoDBMpdwnSePe7WnI9OyObyTeY"
ADMIN_ID = 5927935256

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ----------------------------------------------------
# دیتابیس SQLite
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect('barcode_bot.db')
    cursor = conn.cursor()
    # جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            qr_count INTEGER DEFAULT 0,
            barcode_count INTEGER DEFAULT 0
        )
    ''')
    # جدول تاریخچه بارکدها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            code_type TEXT,
            title TEXT,
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_or_create_user(user_id, username=""):
    conn = sqlite3.connect('barcode_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def add_to_history(user_id, code_type, title, content):
    conn = sqlite3.connect('barcode_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, code_type, title, content) VALUES (?, ?, ?, ?)", 
                   (user_id, code_type, title, content))
    
    if code_type.startswith("QR"):
        cursor.execute("UPDATE users SET qr_count = qr_count + 1 WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("UPDATE users SET barcode_count = barcode_count + 1 WHERE user_id = ?", (user_id,))
        
    conn.commit()
    conn.close()

# ----------------------------------------------------
# وضعیت‌های گفتگو (States)
# ----------------------------------------------------
(
    QR_TEXT_WAIT,
    VCARD_NAME, VCARD_PHONE, VCARD_EMAIL,
    WIFI_SSID, WIFI_PASS,
    BARCODE_128_WAIT,
    BARCODE_EAN_WAIT
) = range(8)

# ----------------------------------------------------
# کیبوردها
# ----------------------------------------------------
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 ساخت QR Code", callback_data="menu_qr"), InlineKeyboardButton("📊 ساخت بارکد خطی", callback_data="menu_barcode")],
        [InlineKeyboardButton("🔍 اسکن تصویر بارکد", callback_data="menu_scan"), InlineKeyboardButton("👤 پنل کاربری و آمار", callback_data="menu_profile")],
    ])

def qr_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 متن یا لینک ساده", callback_data="qr_type_text")],
        [InlineKeyboardButton("📇 کارت ویزیت (vCard)", callback_data="qr_type_vcard")],
        [InlineKeyboardButton("📶 اتصال به وای‌فای (Wi-Fi)", callback_data="qr_type_wifi")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ])

def barcode_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 Code128 (شرکتی / عمومی)", callback_data="bc_type_128")],
        [InlineKeyboardButton("🛒 EAN-13 (۱_۳ رقمی فروشگاهی)", callback_data="bc_type_ean")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ])

# ----------------------------------------------------
# دستور /start
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username)
    text = (
        f"سلام {user.first_name} عزیز! 👋\n\n"
        f"به ربات جامع **سازنده و اسکنر بارکد / QR Code** خوش آمدید.\n"
        f"لطفاً خدمت مورد نظر خود را از منوی زیر انتخاب کنید:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())
    else:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_keyboard())

# ----------------------------------------------------
# مدیریت کلیک‌ها
# ----------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await start_command(update, context)

    elif data == "menu_qr":
        await query.edit_message_text("📱 **نوع QR Code مورد نظر خود را انتخاب کنید:**", parse_mode="Markdown", reply_markup=qr_keyboard())

    elif data == "menu_barcode":
        await query.edit_message_text("📊 **نوع بارکد خطی مورد نظر را انتخاب کنید:**", parse_mode="Markdown", reply_markup=barcode_keyboard())

    elif data == "menu_scan":
        text = "🔍 **اسکنر بارکد و QR Code**\n\nکافیست تصویر (عکس) حاوی بارکد یا QR کد را به همین چت ارسال کنید تا محتوای آن استخراج شود."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    elif data == "menu_profile":
        u = get_or_create_user(user_id)
        conn = sqlite3.connect('barcode_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, code_type, title FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 10", (user_id,))
        history = cursor.fetchall()
        conn.close()

        text = (
            f"👤 **پنل کاربری**\n\n"
            f"🆔 شناسه: `{u[0]}`\n"
            f"📱 QR کدهای ساخته شده: **{u[2]}**\n"
            f"📊 بارکدهای خطی ساخته شده: **{u[3]}**\n"
            f"🔢 مجموع کل: **{u[2] + u[3]}**\n\n"
            f"📜 **۱۰ ساخت اخیر شما:**\n"
        )
        
        kb_list = []
        if not history:
            text += "هیچ تاریخی ثبت نشده است."
        else:
            for h in history:
                text += f"🔹 [{h[1]}] {h[2]}\n"
                kb_list.append([InlineKeyboardButton(f"📥 دریافت مجدد: {h[2]}", callback_data=f"reget_{h[0]}")])

        kb_list.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb_list))

    elif data.startswith("reget_"):
        h_id = int(data.split("_")[1])
        conn = sqlite3.connect('barcode_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT code_type, content, title FROM history WHERE id = ?", (h_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            await generate_and_send_code(query.message, user_id, row[0], row[1], row[2], is_reget=True)

# ----------------------------------------------------
# تابع عمومی ساخت و ارسال تصویر کد
# ----------------------------------------------------
async def generate_and_send_code(message_obj, user_id, code_type, content, title, is_reget=False):
    bio = io.BytesIO()

    if code_type.startswith("QR"):
        qr = qrcode.QRCode(version=1, box_size=10, border=3)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(bio, format='PNG')
    else:
        if code_type == "BARCODE_128":
            bc_class = barcode.get_barcode_class('code128')
        else:
            bc_class = barcode.get_barcode_class('ean13')
        
        bc = bc_class(content, writer=ImageWriter())
        bc.write(bio)

    bio.seek(0)
    
    if not is_reget:
        add_to_history(user_id, code_type, title, content)

    caption = f"✅ **{title}** با موفقیت ساخته شد!\n\n🔹 نوع: `{code_type}`"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]])
    await message_obj.reply_photo(photo=bio, caption=caption, parse_mode="Markdown", reply_markup=kb)

# ----------------------------------------------------
# گفتگوها (Conversations)
# ----------------------------------------------------
# ۱. QR متنی
async def qr_text_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("لطفاً متن یا لینک خود را ارسال کنید:")
    return QR_TEXT_WAIT

async def qr_text_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    title = text[:15] + "..." if len(text) > 15 else text
    await generate_and_send_code(update.message, user_id, "QR_TEXT", text, f"QR متنی: {title}")
    return ConversationHandler.END

# ۲. کارت ویزیت
async def vcard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("نام و نام خانوادگی را وارد کنید:")
    return VCARD_NAME

async def vcard_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['v_name'] = update.message.text
    await update.message.reply_text("شماره تلفن را وارد کنید (مثال: 09123456789):")
    return VCARD_PHONE

async def vcard_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['v_phone'] = update.message.text
    await update.message.reply_text("آدرس ایمیل را وارد کنید (یا یک متن دلخواه):")
    return VCARD_EMAIL

async def vcard_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['v_name']
    phone = context.user_data['v_phone']
    email = update.message.text
    
    vcard_data = f"BEGIN:VCARD\nVERSION:3.0\nN:{name}\nTEL:{phone}\nEMAIL:{email}\nEND:VCARD"
    user_id = update.effective_user.id
    await generate_and_send_code(update.message, user_id, "QR_VCARD", vcard_data, f"کارت ویزیت: {name}")
    return ConversationHandler.END

# ۳. وای‌فای
async def wifi_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("نام شبکه وای‌فای (SSID) را وارد کنید:")
    return WIFI_SSID

async def wifi_ssid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['w_ssid'] = update.message.text
    await update.message.reply_text("رمز عبور وای‌فای را وارد کنید:")
    return WIFI_PASS

async def wifi_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ssid = context.user_data['w_ssid']
    password = update.message.text
    wifi_data = f"WIFI:S:{ssid};T:WPA;P:{password};;"
    user_id = update.effective_user.id
    await generate_and_send_code(update.message, user_id, "QR_WIFI", wifi_data, f"وای‌فای: {ssid}")
    return ConversationHandler.END

# ۴. بارکد Code128
async def bc128_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("متن یا عدد بارکد (حروف انگلیسی یا عدد) را وارد کنید:")
    return BARCODE_128_WAIT

async def bc128_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    await generate_and_send_code(update.message, user_id, "BARCODE_128", text, f"بارکد 128: {text[:10]}")
    return ConversationHandler.END

# ۵. بارکد EAN-13
async def bcean_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("یک عدد ۱۲ یا ۱۳ رقمی وارد کنید:")
    return BARCODE_EAN_WAIT

async def bcean_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or len(text) not in [12, 13]:
        await update.message.reply_text("❌ خطا! بارکد EAN-13 باید دقیقاً ۱۲ یا ۱۳ رقم عدد باشد. مجدداً تلاش کنید:")
        return BARCODE_EAN_WAIT
    
    user_id = update.effective_user.id
    await generate_and_send_code(update.message, user_id, "BARCODE_EAN13", text[:12], f"بارکد EAN13: {text}")
    return ConversationHandler.END

# ----------------------------------------------------
# هندلر اسکن عکس
# ----------------------------------------------------
async def scan_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = await update.message.photo[-1].get_file()
    photo_bytes = await photo.download_as_bytearray()
    
    img = Image.open(io.BytesIO(photo_bytes))
    decoded_objects = decode(img)

    if not decoded_objects:
        await update.message.reply_text("❌ هیچ بارکد یا QR کدی در این تصویر تشخیص داده نشد.")
    else:
        text = "🔍 **اطلاعات استخراج شده از تصویر:**\n\n"
        for obj in decoded_objects:
            data_str = obj.data.decode('utf-8')
            code_type = obj.type
            text += f"🔹 **نوع کد:** `{code_type}`\n🔑 **محتوا:**\n`{data_str}`\n-------------------\n"
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 منوی اصلی", callback_data="main_menu")]])
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# ----------------------------------------------------
# تابع اصلی
# ----------------------------------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # گفتگوها
    conv_qr_text = ConversationHandler(
        entry_points=[CallbackQueryHandler(qr_text_start, pattern="^qr_type_text$")],
        states={QR_TEXT_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, qr_text_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_vcard = ConversationHandler(
        entry_points=[CallbackQueryHandler(vcard_start, pattern="^qr_type_vcard$")],
        states={
            VCARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, vcard_name)],
            VCARD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, vcard_phone)],
            VCARD_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, vcard_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_wifi = ConversationHandler(
        entry_points=[CallbackQueryHandler(wifi_start, pattern="^qr_type_wifi$")],
        states={
            WIFI_SSID: [MessageHandler(filters.TEXT & ~filters.COMMAND, wifi_ssid)],
            WIFI_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, wifi_pass)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_bc128 = ConversationHandler(
        entry_points=[CallbackQueryHandler(bc128_start, pattern="^bc_type_128$")],
        states={BARCODE_128_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bc128_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_bcean = ConversationHandler(
        entry_points=[CallbackQueryHandler(bcean_start, pattern="^bc_type_ean$")],
        states={BARCODE_EAN_WAIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bcean_finish)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(conv_qr_text)
    app.add_handler(conv_vcard)
    app.add_handler(conv_wifi)
    app.add_handler(conv_bc128)
    app.add_handler(conv_bcean)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, scan_photo_handler))

    print("🚀 ربات بارکد و QR Code با موفقیت فعال شد...")
    app.run_polling()

if __name__ == '__main__':
    main()
