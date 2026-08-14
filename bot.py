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
RCLONE_CONFIG = "/app/rclone.conf"
TOKEN = "8665274076:AAH1b3FPtmYbZIwaMdpVMYbC63LLA3QViU0"
# ---------------------------------------------------------

GET_NAME, GET_TYPE, GET_USER, GET_PASS = range(4)
USER_QUEUES = {}
USER_TASKS = {}

def load_data():
    if os.path.exists(DATA_FILE):
        try: with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS_DATA = load_data()

# این تابع کانفیگ را دستی می‌سازد تا ارور بخش و بک‌اند ندهد
def update_rclone_config():
    with open(RCLONE_CONFIG, "w") as f:
        for uid, udata in USERS_DATA.items():
            for acc_name, acc_info in udata.get("accounts", {}).items():
                f.write(f"[{acc_info['remote']}]\ntype = {acc_info['type']}\nuser = {acc_info['user']}\npass = {acc_info['pass']}\n\n")

def get_user_accounts(user_id):
    str_id = str(user_id)
    if str_id not in USERS_DATA:
        USERS_DATA[str_id] = {"accounts": {}, "active_acc": None, "upload_mode": False}
        save_data(USERS_DATA)
    return USERS_DATA[str_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    is_upload_on = user_info.get("upload_mode", False)
    active_acc = user_info.get("active_acc") or "❌ هیچ اکانتی فعال نیست"
    
    # چیدمان دقیقاً همان چیزی که در اسکرین‌شات اول بود
    keyboard = [
        [InlineKeyboardButton("⏹ توقف فاز آپلود" if is_upload_on else "🚀 شروع فاز آپلود", callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت فعال", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")],
        [InlineKeyboardButton("💎 وضعیت حساب", callback_data="user_status")]
    ]
    text = f"✨ **سیستم مدیریت هوشمند آپلود ابری پیشگام** ✨\n──────────────────────────────\n🎯 **اکانت مقصد فعال:** `{active_acc}`\n⚡ **وضعیت آپلود:** {'🟢 روشن' if is_upload_on else '🔴 خاموش'}\n──────────────────────────────\n👇 برای شروع عملیات گزینه‌ای را انتخاب کنید:"
    
    if update.callback_query: await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# --- سایر توابع فنی بدون تغییر در ظاهر ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    u = get_user_accounts(user_id)

    if data == "back_to_main": await start(update, context)
    elif data == "toggle_upload":
        u["upload_mode"] = not u.get("upload_mode", False)
        save_data(USERS_DATA)
        await start(update, context)
    elif data == "storage_stats":
        if not u.get("active_acc"): await query.edit_message_text("❌ هیچ اکانتی فعال نیست.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
        else:
            remote = u['accounts'][u['active_acc']]['remote']
            res = subprocess.run(["rclone", "size", "--json", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
            stats = json.loads(res.stdout)
            await query.edit_message_text(f"📊 حجم: `{round(stats.get('bytes', 0)/(1024**3), 2)} GB`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
    
    elif data.startswith("setacc_"):
        u['active_acc'] = data.replace("setacc_", "")
        save_data(USERS_DATA)
        await start(update, context)
    elif data.startswith("delacc_"):
        del u["accounts"][data.replace("delacc_", "")]
        update_rclone_config()
        save_data(USERS_DATA)
        await start(update, context)
    elif data == "delete_account_user":
        kb = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f"delacc_{name}")] for name in u.get("accounts", {}).keys()]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚠️ حذف اکانت:", reply_markup=InlineKeyboardMarkup(kb))
    elif data == "user_status":
        await query.edit_message_text(f"💎 تعداد اکانت‌ها: `{len(u.get('accounts', {}))}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

# --- کانورزیشن برای افزودن اکانت (بدون تغییر در ظاهر) ---
async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📝 مرحله ۱: نام اکانت را بنویسید:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text.strip()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("☁️ Mega", callback_data="type_mega"), InlineKeyboardButton("📦 TeraBox", callback_data="type_terabox")]])
    await update.message.reply_text("🌐 نوع سرویس:", reply_markup=kb)
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
    name = context.user_data['new_acc_name']
    uid = str(update.effective_user.id)
    u = get_user_accounts(uid)
    remote = f"rem_{uid}_{len(u['accounts'])}"
    
    u['accounts'][name] = {"remote": remote, "type": context.user_data['new_acc_type'], "user": context.user_data['new_acc_user'], "pass": p}
    update_rclone_config()
    save_data(USERS_DATA)
    
    res = subprocess.run(["rclone", "lsd", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
    if res.returncode == 0:
        u['active_acc'] = name
        save_data(USERS_DATA)
        await update.message.reply_text("🎉 تایید و ثبت شد.")
    else: await update.message.reply_text("❌ خطا در اتصال.")
    return ConversationHandler.END

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    u = get_user_accounts(uid)
    if not u.get('upload_mode'): return
    f = await (update.message.document or update.message.video or update.message.audio or update.message.photo[-1]).get_file()
    name = getattr(update.message.document or update.message.video or update.message.audio, 'file_name', f"file_{uid}")
    if uid not in USER_QUEUES: USER_QUEUES[uid] = []
    USER_QUEUES[uid].append((f, name))
    if uid in USER_TASKS and not USER_TASKS[uid].done(): USER_TASKS[uid].cancel()
    USER_TASKS[uid] = asyncio.create_task(run_upload(uid, context))

async def run_upload(uid, context):
    await asyncio.sleep(3)
    items = USER_QUEUES.pop(uid, [])
    u = get_user_accounts(uid)
    remote = u["accounts"][u['active_acc']]["remote"]
    b_dir = f"./batch_{uid}"
    os.makedirs(b_dir, exist_ok=True)
    for f, n in items: await f.download_to_drive(os.path.join(b_dir, n))
    subprocess.run(["rclone", "copy", f"--config={RCLONE_CONFIG}", b_dir, f"{remote}:/"], capture_output=True)
    shutil.rmtree(b_dir)
    await context.bot.send_message(chat_id=int(uid), text="✅ آپلود انجام شد.")

if __name__ == '__main__':
    update_rclone_config()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(start_add_account, pattern="^add_account$")], states={GET_NAME: [MessageHandler(filters.TEXT, get_name)], GET_TYPE: [CallbackQueryHandler(get_type, pattern="^type_")], GET_USER: [MessageHandler(filters.TEXT, get_user)], GET_PASS: [MessageHandler(filters.TEXT, get_pass)]}, fallbacks=[]))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_files))
    app.run_polling()
