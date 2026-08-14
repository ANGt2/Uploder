from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, ConversationHandler, filters
)
import os, json, logging, subprocess, shutil, asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ---------------------------------------------------------
ADMIN_ID = 5927935256
DATA_FILE = "users_data.json"
RCLONE_CONFIG = "rclone.conf"
TOKEN = "8665274076:AAH1b3FPtmYbZIwaMdpVMYbC63LLA3QViU0"
# ---------------------------------------------------------

GET_NAME, GET_TYPE, GET_USER, GET_PASS = range(4)
USER_QUEUES = {}
USER_TASKS = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS_DATA = load_data()

def update_rclone_config():
    """بازسازی کامل فایل کانفیگ از روی دیتابیس"""
    with open(RCLONE_CONFIG, "w") as f:
        for uid, udata in USERS_DATA.items():
            for acc_name, acc_info in udata.get("accounts", {}).items():
                r_name = acc_info.get("remote")
                s_type = acc_info.get("type", "mega")
                user = acc_info.get("user")
                pwd = acc_info.get("pass")
                f.write(f"[{r_name}]\ntype = {s_type}\nuser = {user}\npass = {pwd}\n\n")

def get_user_accounts(user_id):
    str_id = str(user_id)
    if str_id not in USERS_DATA:
        USERS_DATA[str_id] = {"accounts": {}, "active_acc": None, "upload_mode": False}
        save_data(USERS_DATA)
    return USERS_DATA[str_id]

# --- هندلرهای اصلی ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    is_upload_on = user_info.get("upload_mode", False)
    active_acc = user_info.get("active_acc") or "❌ هیچ اکانتی فعال نیست"
    
    keyboard = [
        [InlineKeyboardButton("⏹ توقف فاز آپلود" if is_upload_on else "🚀 شروع فاز آپلود", callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")],
        [InlineKeyboardButton("💎 وضعیت حساب", callback_data="user_status")]
    ]
    
    text = f"✨ **سیستم مدیریت هوشمند پیشگام**\n🎯 **اکانت فعال:** `{active_acc}`\n⚡ **وضعیت:** {'🟢 روشن' if is_upload_on else '🔴 خاموش'}"
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
        save_data(USERS_DATA)
        await start(update, context)
    
    elif data == "storage_stats":
        active_acc = user_info.get("active_acc")
        if not active_acc:
            await query.edit_message_text("❌ اکانتی انتخاب نشده.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            return
        remote = user_info['accounts'][active_acc]['remote']
        res = subprocess.run(["rclone", "size", "--json", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
        try:
            stats = json.loads(res.stdout)
            await query.edit_message_text(f"📊 **آمار:**\n📁 فایل‌ها: `{stats.get('count', 0)}`\n💾 حجم: `{round(stats.get('bytes', 0)/(1024**3), 2)} GB`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
        except: await query.edit_message_text("❌ خطا در خواندن.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

    elif data.startswith("setacc_"):
        user_info['active_acc'] = data.replace("setacc_", "")
        save_data(USERS_DATA)
        await start(update, context)

    elif data.startswith("delacc_"):
        del user_info["accounts"][data.replace("delacc_", "")]
        update_rclone_config()
        save_data(USERS_DATA)
        await start(update, context)

# --- منطق افزودن اکانت با نوشتن مستقیم فایل ---
async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📝 نام اکانت را بنویسید:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text.strip()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("☁️ Mega", callback_data="type_mega"), InlineKeyboardButton("📦 TeraBox", callback_data="type_terabox")]])
    await update.message.reply_text("🌐 نوع اکانت:", reply_markup=kb)
    return GET_TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_type'] = update.callback_query.data.replace("type_", "")
    await update.callback_query.edit_message_text("📧 ایمیل/کاربری:")
    return GET_USER

async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_user'] = update.message.text.strip()
    await update.message.reply_text("🔑 رمز عبور:")
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.message.text.strip()
    uid = str(update.effective_user.id)
    u = get_user_accounts(uid)
    name = context.user_data['new_acc_name']
    remote = f"rem_{uid}_{len(u['accounts'])}"
    
    # ثبت دستی در دیکشنری و فایل کانفیگ
    u['accounts'][name] = {"remote": remote, "type": context.user_data['new_acc_type'], "user": context.user_data['new_acc_user'], "pass": p}
    update_rclone_config()
    save_data(USERS_DATA)
    
    # تست با دستور lsd و فایل کانفیگ اختصاصی
    res = subprocess.run(["rclone", "lsd", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
    if res.returncode == 0:
        await update.message.reply_text("🎉 اکانت با موفقیت تایید و ثبت شد.")
    else:
        await update.message.reply_text("❌ خطا در تایید اتصال.")
    return ConversationHandler.END

# --- پردازش فایل ---
async def process_batch_queue(user_id, client):
    await asyncio.sleep(2)
    items = USER_QUEUES.pop(user_id, [])
    if not items: return
    u = get_user_accounts(user_id)
    remote = u["accounts"][u['active_acc']]["remote"]
    batch_dir = f"./batch_{user_id}"
    os.makedirs(batch_dir, exist_ok=True)
    
    for tg_f, name in items: await tg_f.download_to_drive(os.path.join(batch_dir, name))
    
    subprocess.run(["rclone", "copy", f"--config={RCLONE_CONFIG}", batch_dir, f"{remote}:/"], capture_output=True)
    shutil.rmtree(batch_dir)
    await client.send_message(user_id, "✅ آپلود تمام شد.")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def handle_files(client, message):
    uid = str(message.from_user.id)
    if not get_user_accounts(uid).get('upload_mode', False): return
    
    tg_f = await message.download()
    name = getattr(message.document or message.video or message.audio, 'file_name', f"file_{uid}")
    if uid not in USER_QUEUES: USER_QUEUES[uid] = []
    USER_QUEUES[uid].append((tg_f, name))
    USER_TASKS[uid] = asyncio.create_task(process_batch_queue(uid, client))

if __name__ == '__main__':
    update_rclone_config()
    app.run()
