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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    active_acc = user_info.get("active_acc") or "❌ فعال نیست"
    keyboard = [[InlineKeyboardButton("🚀 شروع/توقف آپلود", callback_data="toggle_upload")],
                [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account")],
                [InlineKeyboardButton("📊 آمار", callback_data="storage_stats")]]
    text = f"✨ **ربات مدیریت پیشگام**\n🎯 اکانت: `{active_acc}`"
    if update.callback_query: await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u = get_user_accounts(user_id)
    if not u.get('upload_mode'): return
    
    file = await (update.message.document or update.message.video or update.message.audio or update.message.photo[-1]).get_file()
    name = getattr(update.message.document or update.message.video or update.message.audio, 'file_name', f"file_{update.message.date.timestamp()}")
    
    if user_id not in USER_QUEUES: USER_QUEUES[user_id] = []
    USER_QUEUES[user_id].append((file, name))
    
    if user_id in USER_TASKS and not USER_TASKS[user_id].done(): USER_TASKS[user_id].cancel()
    USER_TASKS[user_id] = asyncio.create_task(run_upload(user_id, context))

async def run_upload(user_id, context):
    await asyncio.sleep(3)
    items = USER_QUEUES.pop(user_id, [])
    u = get_user_accounts(user_id)
    remote = u["accounts"][u['active_acc']]["remote"]
    batch_dir = f"./batch_{user_id}"
    os.makedirs(batch_dir, exist_ok=True)
    for f, n in items: await f.download_to_drive(os.path.join(batch_dir, n))
    subprocess.run(["rclone", "copy", f"--config={RCLONE_CONFIG}", batch_dir, f"{remote}:/"], capture_output=True)
    shutil.rmtree(batch_dir)
    await context.bot.send_message(chat_id=int(user_id), text="✅ آپلود انجام شد.")

if __name__ == '__main__':
    update_rclone_config()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lambda u,c: start(u,c), pattern="back_to_main"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_files))
    app.run_polling()
