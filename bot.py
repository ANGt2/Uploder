from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
import os
import json
import logging
import subprocess
import shutil
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ADMIN_ID = 5927935256
DATA_FILE = "users_data.json"
TOKEN = "8665274076:AAH1b3FPtmYbZIwaMdpVMYbC63LLA3QViU0"

GET_NAME, GET_TYPE, GET_USER, GET_PASS = range(4)
USER_QUEUES = {}
USER_TASKS = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data_local(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS_DATA = load_data()

def rebuild_rclone_configs():
    for uid, udata in USERS_DATA.items():
        for acc_name, acc_info in udata.get("accounts", {}).items():
            r_name = acc_info.get("remote")
            s_type = acc_info.get("type", "mega")
            user = acc_info.get("user")
            pwd = acc_info.get("pass")
            if r_name and user and pwd:
                subprocess.run(["rclone", "config", "create", r_name, s_type, f"user={user}", f"pass={pwd}"], capture_output=True, text=True)

async def manual_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_data_local(USERS_DATA)
    with open(DATA_FILE, "rb") as f:
        await context.bot.send_document(chat_id=ADMIN_ID, document=f, caption="💾 بکاپ تنظیمات و اکانت‌ها")

async def restore_data_from_telegram(app):
    global USERS_DATA
    try:
        chat = await app.bot.get_chat(ADMIN_ID)
        # جستجوی فایل بکاپ در تاریخچه (آخرین پیام حاوی فایل)
        async for msg in app.bot.get_chat_history(ADMIN_ID, limit=5):
            if msg.document and "بکاپ تنظیمات" in (msg.caption or ""):
                tg_file = await msg.document.get_file()
                await tg_file.download_to_drive(DATA_FILE)
                USERS_DATA = load_data()
                rebuild_rclone_configs()
                logging.info("🎉 Database restored successfully!")
                break
    except Exception as e:
        logging.error(f"Restore check error: {e}")

def get_user_accounts(user_id):
    str_id = str(user_id)
    if str_id not in USERS_DATA:
        USERS_DATA[str_id] = {"accounts": {}, "active_acc": None, "upload_mode": False}
        save_data_local(USERS_DATA)
    return USERS_DATA[str_id]

async def safe_send_text(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str):
    while len(text) > 0:
        chunk = text[:1500]
        text = text[1500:]
        try:
            await context.bot.send_message(chat_id=chat_id, text=chunk, disable_web_page_preview=True)
        except Exception:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    is_upload_on = user_info.get("upload_mode", False)
    active_acc = user_info.get("active_acc") or "❌ فعال نیست"

    keyboard = [
        [InlineKeyboardButton("⏹ توقف" if is_upload_on else "🚀 شروع فاز آپلود", callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")],
        [InlineKeyboardButton("💎 وضعیت حساب", callback_data="user_status")]
    ]
    text = f"✨ **سیستم آپلود ابری**\n🎯 **اکانت فعال:** `{active_acc}`\n⚡ **وضعیت:** {'🟢 روشن' if is_upload_on else '🔴 خاموش'}"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)

    if data == "back_to_main":
        await start(update, context)
    elif data == "toggle_upload":
        user_info["upload_mode"] = not user_info.get("upload_mode", False)
        save_data_local(USERS_DATA)
        await start(update, context)
    elif data == "storage_stats":
        active_acc = user_info.get("active_acc")
        if not active_acc:
            await query.edit_message_text("❌ اکانت فعالی انتخاب نشده.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            return
        await query.edit_message_text("⏳ در حال محاسبه حجم...")
        remote_name = user_info["accounts"][active_acc]["remote"]
        res = subprocess.run(["rclone", "size", "--json", f"{remote_name}:"], capture_output=True, text=True)
        try:
            stats = json.loads(res.stdout)
            text = f"📊 **آمار:**\n📁 فایل‌ها: `{stats.get('count', 0)}`\n💾 حجم: `{round(stats.get('bytes', 0)/(1024**3), 2)} GB`"
        except:
            text = "❌ خطا در دریافت آمار."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
    
    elif data == "change_account":
        accs = user_info.get("accounts", {})
        if not accs:
            await query.edit_message_text("❌ اکانتی یافت نشد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            return
        keyboard = [[InlineKeyboardButton(f"{'✨ ' if name == user_info.get('active_acc') else ''}{name}", callback_data=f"setacc_{name}")] for name in accs.keys()]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚙️ **انتخاب اکانت فعال:**", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("setacc_"):
        user_info['active_acc'] = data.replace("setacc_", "")
        save_data_local(USERS_DATA)
        await start(update, context)
    
    elif data.startswith("delacc_"):
        acc_name = data.replace("delacc_", "")
        subprocess.run(["rclone", "config", "delete", user_info["accounts"][acc_name]["remote"]], capture_output=True, text=True)
        del user_info["accounts"][acc_name]
        save_data_local(USERS_DATA)
        await start(update, context)
    
    elif data == "delete_account_user":
        keyboard = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f"delacc_{name}")] for name in user_info.get("accounts", {}).keys()]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚠️ **حذف اکانت:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 نام اکانت را بنویسید:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text.strip()
    await update.message.reply_text("🌐 نوع اکانت (mega/terabox):")
    return GET_TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_type'] = update.message.text.strip()
    await update.message.reply_text("📧 ایمیل یا نام‌کاربری:")
    return GET_USER

async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_user'] = update.message.text.strip()
    await update.message.reply_text("🔑 رمز عبور:")
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc_pass = update.message.text.strip()
    acc_name = context.user_data['new_acc_name']
    srv_type = context.user_data['new_acc_type']
    acc_user = context.user_data['new_acc_user']
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    remote_name = f"u{user_id}_{len(user_info['accounts']) + 1}"
    
    subprocess.run(["rclone", "config", "create", remote_name, srv_type, f"user={acc_user}", f"pass={acc_pass}"], capture_output=True, text=True)
    user_info['accounts'][acc_name] = {"remote": remote_name, "type": srv_type, "user": acc_user, "pass": acc_pass, "path": f"{remote_name}:/"}
    user_info['active_acc'] = acc_name
    save_data_local(USERS_DATA)
    await update.message.reply_text("🎉 اکانت اضافه شد.")
    return ConversationHandler.END

async def process_batch_queue(user_id: str, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(2.5)
    items = USER_QUEUES.pop(user_id, [])
    USER_TASKS.pop(user_id, None)
    if not items: return
    
    user_info = get_user_accounts(user_id)
    active_acc = user_info.get("active_acc")
    target = user_info["accounts"][active_acc]["path"]
    
    batch_dir = f"./batch_{user_id}"
    os.makedirs(batch_dir, exist_ok=True)
    msg = await context.bot.send_message(chat_id=int(user_id), text="⚡ در حال آپلود...")
    
    for tg_file, fname in items:
        await tg_file.download_to_drive(os.path.join(batch_dir, fname))
    
    subprocess.run(["rclone", "copy", batch_dir, target, "--transfers", "4", "--buffer-size", "64M"], capture_output=True, text=True)
    await msg.delete()
    await safe_send_text(context, int(user_id), "✅ آپلود تمام شد.")
    shutil.rmtree(batch_dir)

async def handle_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    if not user_info.get('upload_mode', False): return
    
    tg_file = await (update.message.document or update.message.video or update.message.audio or update.message.photo[-1]).get_file()
    fname = getattr(update.message.document or update.message.video or update.message.audio, 'file_name', f"file_{update.message.date.timestamp()}")
    
    if user_id not in USER_QUEUES: USER_QUEUES[user_id] = []
    USER_QUEUES[user_id].append((tg_file, fname))
    if user_id in USER_TASKS and not USER_TASKS[user_id].done(): USER_TASKS[user_id].cancel()
    USER_TASKS[user_id] = asyncio.create_task(process_batch_queue(user_id, context))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(lambda app: restore_data_from_telegram(app)).build()
    # (Handlers remain same...)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("backup", manual_backup))
    app.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(start_add_account, pattern="^add_account$")], states={GET_NAME: [MessageHandler(filters.TEXT, get_name)], GET_TYPE: [MessageHandler(filters.TEXT, get_type)], GET_USER: [MessageHandler(filters.TEXT, get_user)], GET_PASS: [MessageHandler(filters.TEXT, get_pass)]}, fallbacks=[CommandHandler('cancel', lambda u,c: start(u,c))]))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_files))
    app.run_polling()
