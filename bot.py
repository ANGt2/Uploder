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
    """بازسازی فایل کانفیگ با فرمت استاندارد"""
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
    is_upload_on = user_info.get("upload_mode", False)
    active_acc = user_info.get("active_acc") or "❌ فعال نیست"
    kb = [
        [InlineKeyboardButton("⏹ توقف" if is_upload_on else "🚀 شروع فاز آپلود", callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")],
        [InlineKeyboardButton("💎 وضعیت حساب", callback_data="user_status")]
    ]
    text = f"✨ **سیستم مدیریت هوشمند پیشگام**\n🎯 **اکانت مقصد:** `{active_acc}`\n⚡ **وضعیت:** {'🟢 روشن' if is_upload_on else '🔴 خاموش'}"
    if update.callback_query: await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    else: await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

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
            await query.edit_message_text("❌ ابتدا یک اکانت فعال کنید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
            return
        remote = user_info['accounts'][active_acc]['remote']
        # اجرای rclone با تعیین صریح config
        res = subprocess.run(["rclone", "size", "--json", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
        try:
            stats = json.loads(res.stdout)
            await query.edit_message_text(f"📊 **آمار:** `{round(stats.get('bytes', 0)/(1024**3), 2)} GB`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
        except: await query.edit_message_text("❌ خطا.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))
    
    elif data.startswith("setacc_"):
        user_info['active_acc'] = data.replace("setacc_", "")
        save_data(USERS_DATA)
        await start(update, context)
    elif data.startswith("delacc_"):
        del user_info["accounts"][data.replace("delacc_", "")]
        update_rclone_config()
        save_data(USERS_DATA)
        await start(update, context)
    elif data == "delete_account_user":
        kb = [[InlineKeyboardButton(f"🗑 {name}", callback_data=f"delacc_{name}")] for name in user_info.get("accounts", {}).keys()]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚠️ حذف:", reply_markup=InlineKeyboardMarkup(kb))
    elif data == "user_status":
        text = f"💎 **شناسنامه:**\nتعداد اکانت: `{len(user_info.get('accounts', {}))}`"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]))

# --- کانورزیشن هندلر ---
async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📝 نام اکانت را بنویسید:")
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
    
    # ثبت در دیکشنری و فایل کانفیگ
    u['accounts'][name] = {"remote": remote, "type": context.user_data['new_acc_type'], "user": context.user_data['new_acc_user'], "pass": p}
    update_rclone_config()
    save_data(USERS_DATA)
    
    # تست اتصال با فایل کانفیگ اختصاصی
    res = subprocess.run(["rclone", "lsd", f"--config={RCLONE_CONFIG}", f"{remote}:"], capture_output=True, text=True)
    if res.returncode == 0:
        u['active_acc'] = name
        save_data(USERS_DATA)
        await update.message.reply_text("🎉 اکانت ثبت و تایید شد.")
    else:
        await update.message.reply_text(f"❌ خطا در اتصال:\n`{res.stderr}`", parse_mode="Markdown")
    return ConversationHandler.END

# --- فایل‌ها ---
async def run_upload(user_id, context, items):
    u = get_user_accounts(user_id)
    remote = u["accounts"][u['active_acc']]["remote"]
    batch_dir = f"./batch_{user_id}"
    os.makedirs(batch_dir, exist_ok=True)
    for f, n in items: await f.download_to_drive(os.path.join(batch_dir, n))
    
    subprocess.run(["rclone", "copy", f"--config={RCLONE_CONFIG}", batch_dir, f"{remote}:/"], capture_output=True)
    shutil.rmtree(batch_dir)
    await context.bot.send_message(chat_id=int(user_id), text="✅ آپلود انجام شد.")

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not get_user_accounts(uid).get('upload_mode'): return
    file = await (update.message.document or update.message.video or update.message.audio or update.message.photo[-1]).get_file()
    name = getattr(update.message.document or update.message.video or update.message.audio, 'file_name', f"f_{uid}")
    if uid not in USER_QUEUES: USER_QUEUES[uid] = []
    USER_QUEUES[uid].append((file, name))
    if uid in USER_TASKS and not USER_TASKS[uid].done(): USER_TASKS[uid].cancel()
    USER_TASKS[uid] = asyncio.create_task(run_upload(uid, context, USER_QUEUES.pop(uid)))

if __name__ == '__main__':
    update_rclone_config()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(start_add_account, pattern="^add_account$")], 
                                        states={GET_NAME: [MessageHandler(filters.TEXT, get_name)], GET_TYPE: [CallbackQueryHandler(get_type, pattern="^type_")], GET_USER: [MessageHandler(filters.TEXT, get_user)], GET_PASS: [MessageHandler(filters.TEXT, get_pass)]}, fallbacks=[]))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_files))
    app.run_polling()
