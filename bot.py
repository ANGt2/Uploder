from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
import os, json, logging, subprocess, shutil, asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

ADMIN_ID = 5927935256
DATA_FILE = "users_data.json"
TOKEN = "8665274076:AAH1b3FPtmYbZIwaMdpVMYbC63LLA3QViU0"

GET_NAME, GET_TYPE, GET_USER, GET_PASS = range(4)
USER_QUEUES = {}
USER_TASKS = {}

# --- سیستم بکاپ و بازیابی ابری ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: return {}
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
        async for msg in app.bot.get_chat_history(ADMIN_ID, limit=5):
            if msg.document and "بکاپ تنظیمات" in (msg.caption or ""):
                tg_file = await msg.document.get_file()
                await tg_file.download_to_drive(DATA_FILE)
                USERS_DATA = load_data()
                rebuild_rclone_configs()
                break
    except Exception as e: logging.error(f"Restore error: {e}")

# --- توابع ربات ---
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
        try: await context.bot.send_message(chat_id=chat_id, text=chunk, disable_web_page_preview=True)
        except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    is_upload_on = user_info.get("upload_mode", False)
    active_acc = user_info.get("active_acc") or "❌ فعال نیست"
    keyboard = [
        [InlineKeyboardButton("⏹ توقف" if is_upload_on else "🚀 شروع فاز آپلود", callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")]
    ]
    text = f"✨ **مدیریت ابری**\n🎯 **اکانت فعال:** `{active_acc}`\n⚡ **وضعیت:** {'🟢 روشن' if is_upload_on else '🔴 خاموش'}"
    if update.callback_query: await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    
    if data == "back_to_main": await start(update, context)
    elif data == "toggle_upload":
        user_info["upload_mode"] = not user_info.get("upload_mode", False)
        save_data_local(USERS_DATA)
        await start(update, context)
    elif data == "storage_stats":
        active_acc = user_info.get("active_acc")
        if not active_acc:
            await query.edit_message_text("❌ ابتدا یک اکانت انتخاب کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            return
        await query.edit_message_text("⏳ در حال محاسبه...")
        res = subprocess.run(["rclone", "size", "--json", f"{user_info['accounts'][active_acc]['remote']}:"], capture_output=True, text=True)
        try:
            stats = json.loads(res.stdout)
            await query.edit_message_text(f"📊 **آمار:**\n📁 فایل‌ها: `{stats.get('count', 0)}`\n💾 حجم: `{round(stats.get('bytes', 0)/(1024**3), 2)} GB`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
        except: await query.edit_message_text("❌ خطا.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
    
    elif data == "change_account":
        accs = user_info.get("accounts", {})
        keyboard = [[InlineKeyboardButton(f"{'✨ ' if name == user_info.get('active_acc') else ''}{name}", callback_data=f"setacc_{name}")] for name in accs.keys()]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚙️ **اکانت فعال را انتخاب کنید:**", reply_markup=InlineKeyboardMarkup(keyboard))
    
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

# --- افزودن اکانت (Conversation Handler) ---
async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📝 نام اکانت را بنویسید:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("☁️ Mega", callback_data="type_mega"), InlineKeyboardButton("📦 TeraBox", callback_data="type_terabox")]
    ])
    await update.message.reply_text("🌐 نوع سرویس:", reply_markup=kb)
    return GET_TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_type'] = update.callback_query.data.replace("type_", "")
    await update.callback_query.edit_message_text("📧 ایمیل/نام کاربری:")
    return GET_USER

async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_user'] = update.message.text
    await update.message.reply_text("🔑 رمز عبور:")
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.message.text
    user_id = str(update.effective_user.id)
    u = get_user_accounts(user_id)
    r = f"u{user_id}_{len(u['accounts'])+1}"
    subprocess.run(["rclone", "config", "create", r, context.user_data['new_acc_type'], f"user={context.user_data['new_acc_user']}", f"pass={p}"], capture_output=True)
    u['accounts'][context.user_data['new_acc_name']] = {"remote": r, "type": context.user_data['new_acc_type'], "user": context.user_data['new_acc_user'], "pass": p, "path": f"{r}:/"}
    u['active_acc'] = context.user_data['new_acc_name']
    save_data_local(USERS_DATA)
    await update.message.reply_text("🎉 اکانت با موفقیت اضافه شد.")
    return ConversationHandler.END

# --- پردازش فایل ---
async def process_batch_queue(user_id, context):
    await asyncio.sleep(2.5)
    items = USER_QUEUES.pop(user_id, [])
    if not items: return
    u = get_user_accounts(user_id)
    target = u["accounts"][u['active_acc']]["path"]
    batch_dir = f"./batch_{user_id}"
    os.makedirs(batch_dir, exist_ok=True)
    for tg_f, name in items: await tg_f.download_to_drive(os.path.join(batch_dir, name))
    subprocess.run(["rclone", "copy", batch_dir, target, "--transfers", "4", "--buffer-size", "64M", "--fast-list"], capture_output=True)
    shutil.rmtree(batch_dir)
    await safe_send_text(context, int(user_id), "✅ آپلود انجام شد.")

async def handle_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not get_user_accounts(uid).get('upload_mode', False): return
    tg_f = await (update.message.document or update.message.video or update.message.audio or update.message.photo[-1]).get_file()
    name = getattr(update.message.document or update.message.video or update.message.audio, 'file_name', f"file_{update.message.date.timestamp()}")
    if uid not in USER_QUEUES: USER_QUEUES[uid] = []
    USER_QUEUES[uid].append((tg_f, name))
    if uid in USER_TASKS and not USER_TASKS[uid].done(): USER_TASKS[uid].cancel()
    USER_TASKS[uid] = asyncio.create_task(process_batch_queue(uid, context))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(restore_data_from_telegram).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("backup", manual_backup))
    app.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(start_add_account, pattern="^add_account$")], states={GET_NAME: [MessageHandler(filters.TEXT, get_name)], GET_TYPE: [CallbackQueryHandler(get_type, pattern="^type_")], GET_USER: [MessageHandler(filters.TEXT, get_user)], GET_PASS: [MessageHandler(filters.TEXT, get_pass)]}, fallbacks=[]))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_files))
    app.run_polling()
