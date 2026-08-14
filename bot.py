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

# ---------------------------------------------------------
ADMIN_ID = 5927935256
DATA_FILE = "users_data.json"
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
        except Exception:
            return {}
    return {}

def save_data(data):
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
                subprocess.run(
                    ["rclone", "config", "create", r_name, s_type, f"user={user}", f"pass={pwd}"],
                    capture_output=True, text=True
                )

def get_user_accounts(user_id):
    str_id = str(user_id)
    if str_id not in USERS_DATA:
        USERS_DATA[str_id] = {"accounts": {}, "active_acc": None, "upload_mode": False}
        save_data(USERS_DATA)
    if "upload_mode" not in USERS_DATA[str_id]:
        USERS_DATA[str_id]["upload_mode"] = False
        save_data(USERS_DATA)
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
    active_acc = user_info.get("active_acc") or "❌ هیچ اکانتی فعال نیست"

    upload_status = "🟢 روشن (آماده دریافت تکی یا گروهی)" if is_upload_on else "🔴 خاموش"
    upload_btn_text = "⏹ توقف فاز آپلود" if is_upload_on else "🚀 شروع فاز آپلود فایل"

    keyboard = [
        [InlineKeyboardButton(upload_btn_text, callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account"), InlineKeyboardButton("📊 آمار حافظه", callback_data="storage_stats")],
        [InlineKeyboardButton("🔄 تغییر اکانت فعال", callback_data="change_account"), InlineKeyboardButton("🗑 حذف اکانت", callback_data="delete_account_user")],
        [InlineKeyboardButton("💎 وضعیت حساب", callback_data="user_status")]
    ]

    text = (
        "✨ **سیستم مدیریت هوشمند آپلود ابری پیشگام** ✨\n"
        "──────────────────────────────\n"
        f"🎯 **اکانت مقصد فعال:** `{active_acc}`\n"
        f"⚡ **وضعیت آپلود:** {upload_status}\n"
        "──────────────────────────────\n"
        "👇 برای شروع عملیات گزینه‌ای را انتخاب کنید:"
    )

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت را ندارید.")
        return

    total_users = len(USERS_DATA)
    keyboard = [
        [InlineKeyboardButton("📊 وضعیت سخت‌افزار سرور", callback_data="server_status")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👑 **پنل فرماندهی ادمین**\n"
        "────────────────────\n"
        f"👥 **تعداد کاربران ثبت‌شده:** `{total_users}` نفر",
        parse_mode="Markdown", reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)

    if data == "back_to_main":
        await start(update, context)

    elif data == "toggle_upload":
        if not user_info.get("active_acc"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account")]])
            await query.edit_message_text("⚠️ **خطا:** ابتدا باید یک اکانت اضافه و فعال کنید.", reply_markup=kb)
            return

        user_info["upload_mode"] = not user_info.get("upload_mode", False)
        save_data(USERS_DATA)
        await start(update, context)

    elif data == "storage_stats":
        active_acc = user_info.get("active_acc")
        if not active_acc or active_acc not in user_info.get("accounts", {}):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
            await query.edit_message_text("❌ هیچ اکانت فعالی برای دریافت آمار انتخاب نشده است.", reply_markup=kb)
            return

        await query.edit_message_text("⏳ **در حال محاسبه حجم مصرفی...**", parse_mode="Markdown")
        remote_name = user_info["accounts"][active_acc]["remote"]
        res = subprocess.run(["rclone", "size", "--json", f"{remote_name}:"], capture_output=True, text=True)

        try:
            stats = json.loads(res.stdout)
            bytes_used = stats.get('bytes', 0)
            count = stats.get('count', 0)
            size_gb = round(bytes_used / (1024 ** 3), 2)
            size_mb = round(bytes_used / (1024 ** 2), 2)
            size_text = f"`{size_gb} GB` ({size_mb} MB)" if size_gb >= 0.1 else f"`{size_mb} MB`"

            text = (
                f"📊 **آمار لحظه‌ای اکانت:** `{active_acc}`\n"
                "──────────────────────\n"
                f"📁 **تعداد فایل‌ها:** `{count}` عدد\n"
                f"💾 **فضای مصرف‌شده:** {size_text}\n"
                "──────────────────────"
            )
        except Exception:
            text = "❌ خطایی در خواندن اطلاعات رخ داد."

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    elif data == "change_account":
        accs = user_info.get("accounts", {})
        if not accs:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ افزودن اکانت", callback_data="add_account")], [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
            await query.edit_message_text("❌ هیچ اکانتی یافت نشد.", reply_markup=kb)
            return

        keyboard = []
        active = user_info.get("active_acc")
        for name in accs.keys():
            label = f"✨ {name} (فعال)" if name == active else f"🔹 {name}"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"setacc_{name}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚙️ **یکی از اکانت‌های زیر را جهت آپلود فعال کنید:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("setacc_"):
        acc_name = data.replace("setacc_", "")
        user_info['active_acc'] = acc_name
        save_data(USERS_DATA)
        await start(update, context)

    elif data == "delete_account_user":
        accs = user_info.get("accounts", {})
        if not accs:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
            await query.edit_message_text("❌ اکانتی برای حذف وجود ندارد.", reply_markup=kb)
            return

        keyboard = []
        for name in accs.keys():
            keyboard.append([InlineKeyboardButton(f"🗑 حذف {name}", callback_data=f"delacc_{name}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
        await query.edit_message_text("⚠️ **انتخاب اکانت جهت حذف دائمی:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("delacc_"):
        acc_name = data.replace("delacc_", "")
        acc_info = user_info["accounts"].get(acc_name)
        if acc_info:
            subprocess.run(["rclone", "config", "delete", acc_info["remote"]], capture_output=True, text=True)
            del user_info["accounts"][acc_name]
            if user_info.get("active_acc") == acc_name:
                user_info["active_acc"] = list(user_info["accounts"].keys())[0] if user_info["accounts"] else None
            save_data(USERS_DATA)

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])
        await query.edit_message_text(f"🗑 اکانت **{acc_name}** با موفقیت حذف گردید.", parse_mode="Markdown", reply_markup=kb)

    elif data == "user_status":
        accs_count = len(user_info.get("accounts", {}))
        active = user_info.get("active_acc") or "هیچ‌کدام"
        mode_str = "🟢 روشن" if user_info.get("upload_mode") else "🔴 خاموش"
        text = (
            "💎 **شناسنامه حساب کاربری شما**\n"
            "──────────────────\n"
            f"🆔 **آیدی تلگرام:** `{user_id}`\n"
            f"📂 **تعداد کل اکانت‌ها:** `{accs_count}`\n"
            f"🎯 **اکانت فعال:** `{active}`\n"
            f"⚡ **وضعیت فاز آپلود:** {mode_str}"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

    elif data == "server_status":
        if update.effective_user.id != ADMIN_ID: return
        total, used, free = shutil.disk_usage("/")
        text = (
            "💻 **وضعیت سخت‌افزاری سرور**\n"
            "──────────────────\n"
            f"🟢 **حافظه آزاد:** `{round(free/(1024**3), 2)} GB`\n"
            f"🔴 **حافظه مصرف‌شده:** `{round(used/(1024**3), 2)} GB`\n"
            f"📦 **حافظه کل سیستم:** `{round(total/(1024**3), 2)} GB`"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]])
    await query.edit_message_text("📝 **مرحله ۱ از ۴:** یک عنوان اختصاصی برای این اکانت بنویسید (مثلاً: `مگای شخصی`):", parse_mode="Markdown", reply_markup=kb)
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("☁️ Mega (مگا)", callback_data="type_mega"), InlineKeyboardButton("📦 TeraBox (تراباکس)", callback_data="type_terabox")],
        [InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]
    ]
    await update.message.reply_text("🌐 **مرحله ۲ از ۴:** سرویس ابری مورد نظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GET_TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['new_acc_type'] = "mega" if query.data == "type_mega" else "terabox"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]])
    await query.edit_message_text("📧 **مرحله ۳ از ۴:** ایمیل یا نام‌کاربری حساب را وارد کنید:", reply_markup=kb)
    return GET_USER

async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_user = update.message.text.strip()
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    srv_type = context.user_data.get('new_acc_type', 'mega')

    for acc_n, acc_d in user_info.get("accounts", {}).items():
        if acc_d.get("user", "").lower() == input_user.lower() and acc_d.get("type", "") == srv_type:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])
            await update.message.reply_text(
                f"⚠️ **این اکانت قبلاً با نام «{acc_n}» ثبت شده است!**\n\nامکان افزودن مجدد یک ایمیل تکراری وجود ندارد.",
                parse_mode="Markdown",
                reply_markup=kb
            )
            return ConversationHandler.END

    context.user_data['new_acc_user'] = input_user
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]])
    await update.message.reply_text("🔑 **مرحله ۴ از ۴:** رمز عبور (Password) حساب را وارد کنید:", reply_markup=kb)
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc_pass = update.message.text.strip()
    acc_name = context.user_data['new_acc_name']
    srv_type = context.user_data['new_acc_type']
    acc_user = context.user_data['new_acc_user']
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)

    remote_name = f"u{user_id}_{len(user_info['accounts']) + 1}"
    msg = await update.message.reply_text("⚡ **در حال بررسی و اعتبارسنجی اتصال به اکانت...**", parse_mode="Markdown")

    obs = subprocess.run(["rclone", "obscure", acc_pass], capture_output=True, text=True)
    obs_pass = obs.stdout.strip() if obs.returncode == 0 else acc_pass

    subprocess.run(["rclone", "config", "create", remote_name, srv_type, f"user={acc_user}", f"pass={obs_pass}"], capture_output=True, text=True)

    res = subprocess.run(["rclone", "lsd", f"{remote_name}:"], capture_output=True, text=True)

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])

    if res.returncode == 0:
        user_info['accounts'][acc_name] = {
            "remote": remote_name,
            "type": srv_type,
            "user": acc_user,
            "pass": obs_pass,
            "path": f"{remote_name}:/"
        }
        user_info['active_acc'] = acc_name
        save_data(USERS_DATA)
        await msg.edit_text(f"🎉 **تبریک!** اکانت **{acc_name}** با موفقیت اضافه و تایید شد.", parse_mode="Markdown", reply_markup=kb)
    else:
        subprocess.run(["rclone", "config", "delete", remote_name], capture_output=True, text=True)
        err = res.stderr.strip() if res.stderr else res.stdout.strip()
        await msg.edit_text(f"❌ **اتصال ناموفق بود!**\n\n🔍 **پاسخ سرور:**\n`{err}`", parse_mode="Markdown", reply_markup=kb)
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

async def process_batch_queue(user_id: str, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(2.5)

    items = USER_QUEUES.pop(user_id, [])
    USER_TASKS.pop(user_id, None)

    if not items:
        return

    user_info = get_user_accounts(user_id)
    active_acc = user_info.get("active_acc")
    if not active_acc or active_acc not in user_info.get("accounts", {}):
        await context.bot.send_message(chat_id=int(user_id), text="❌ اکانت فعالی برای آپلود یافت نشد.")
        return

    target = user_info["accounts"][active_acc]["path"]
    remote_name = user_info["accounts"][active_acc]["remote"]

    count = len(items)
    batch_dir = f"./temp_batch_{user_id}_{int(asyncio.get_event_loop().time())}"
    os.makedirs(batch_dir, exist_ok=True)

    status_msg = await context.bot.send_message(
        chat_id=int(user_id),
        text=f"⚡ دریافت {count} فایل آغاز شد..."
    )

    downloaded_files = []
    total_bytes = 0

    try:
        for idx, item in enumerate(items, 1):
            tg_file, original_name = item
            clean_name = f"f_{idx}_{original_name}"
            save_path = os.path.join(batch_dir, clean_name)

            await tg_file.download_to_drive(save_path)
            total_bytes += os.path.getsize(save_path)
            downloaded_files.append(clean_name)

        total_mb = round(total_bytes / (1024 * 1024), 2)
        try:
            await status_msg.edit_text(f"☁️ انتقال {count} فایل ({total_mb} MB) به {active_acc}...")
        except Exception:
            pass

        upload_cmd = [
            "rclone", "copy", batch_dir, target,
            "--transfers", "4",
            "--buffer-size", "64M",
            "--fast-list"
        ]
        res = subprocess.run(upload_cmd, capture_output=True, text=True)

        if res.returncode == 0:
            try:
                await status_msg.delete()
            except Exception:
                pass

            report = f"✅ آپلود {count} فایل با موفقیت انجام شد ({total_mb} MB):\n\n"
            for fname in downloaded_files:
                link_cmd = ["rclone", "link", f"{remote_name}:{fname}"]
                l_res = subprocess.run(link_cmd, capture_output=True, text=True)
                url = l_res.stdout.strip()
                if url.startswith("http"):
                    report += f"📄 {fname}\n🔗 {url}\n\n"
                else:
                    report += f"📄 {fname} (ذخیره شد)\n\n"

            report += "🟢 فاز آپلود فعال است."
            await safe_send_text(context, int(user_id), report)

        else:
            err_msg = res.stderr.strip()[:200]
            await status_msg.edit_text(f"❌ خطا هنگام انتقال:\n{err_msg}")

    except Exception as e:
        clean_err = str(e)[:200]
        await context.bot.send_message(chat_id=int(user_id), text=f"❌ خطا: {clean_err}")
    finally:
        if os.path.exists(batch_dir):
            shutil.rmtree(batch_dir)

async def handle_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)

    if not user_info.get('upload_mode', False):
        await msg.reply_text("⚠️ فاز آپلود خاموش است! /start را بزنید و فاز آپلود را روشن کنید.")
        return

    tg_file = None
    file_name = f"file_{int(asyncio.get_event_loop().time())}"

    if msg.document:
        tg_file = await msg.document.get_file()
        file_name = msg.document.file_name or f"doc_{msg.document.file_id[:6]}"
    elif msg.video:
        tg_file = await msg.video.get_file()
        file_name = msg.video.file_name or f"video_{msg.video.file_id[:6]}.mp4"
    elif msg.audio:
        tg_file = await msg.audio.get_file()
        file_name = msg.audio.file_name or f"audio_{msg.audio.file_id[:6]}.mp3"
    elif msg.photo:
        tg_file = await msg.photo[-1].get_file()
        file_name = f"photo_{msg.photo[-1].file_id[:6]}.jpg"
    elif msg.voice:
        tg_file = await msg.voice.get_file()
        file_name = f"voice_{msg.voice.file_id[:6]}.ogg"
    elif msg.video_note:
        tg_file = await msg.video_note.get_file()
        file_name = f"videonote_{msg.video_note.file_id[:6]}.mp4"
    else:
        return

    if user_id not in USER_QUEUES:
        USER_QUEUES[user_id] = []

    USER_QUEUES[user_id].append((tg_file, file_name))

    if user_id in USER_TASKS and not USER_TASKS[user_id].done():
        USER_TASKS[user_id].cancel()

    USER_TASKS[user_id] = asyncio.create_task(process_batch_queue(user_id, context))

async def post_init(application):
    rebuild_rclone_configs()

if __name__ == '__main__':
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .read_timeout(120)
        .write_timeout(120)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_account, pattern="^add_account$")],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_TYPE: [CallbackQueryHandler(get_type, pattern="^type_")],
            GET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user)],
            GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conv),
            CallbackQueryHandler(cancel_conv, pattern="^cancel_conv$")
        ]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_files))

    print("🚀 ربات به صورت پایدار و ۱۰۰٪ آنلاین روشن شد...")
    app.run_polling()
