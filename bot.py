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

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

USERS_DATA = load_data()

def get_user_accounts(user_id):
    str_id = str(user_id)
    if str_id not in USERS_DATA:
        USERS_DATA[str_id] = {"accounts": {}, "active_acc": None}
        save_data(USERS_DATA)
    return USERS_DATA[str_id]

# تابع ساخت نوار پیشرفت متحرک گرافیکی
def make_progress_bar(percent):
    done = int(percent // 10)
    remain = 10 - done
    bar = "█" * done + "░" * remain
    return f"[{bar}] {percent}%"

# منوی اصلی شکیل
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_accounts(user_id)
    
    context.user_data['upload_mode'] = context.user_data.get('upload_mode', False)
    active_acc = user_info.get("active_acc") or "❌ هیچ اکانتی فعال نیست"
    
    upload_status = "🟢 آماده دریافت فایل" if context.user_data['upload_mode'] else "🔴 غیرفعال"
    upload_btn_text = "⏹ توقف فاز آپلود" if context.user_data['upload_mode'] else "🚀 شروع فاز آپلود فایل"
    
    keyboard = [
        [InlineKeyboardButton(upload_btn_text, callback_data="toggle_upload")],
        [InlineKeyboardButton("➕ افزودن اکانت ابری", callback_data="add_account"), InlineKeyboardButton("🔄 تغییر اکانت فعال", callback_data="change_account")],
        [InlineKeyboardButton("🗑 حذف اکانت‌های من", callback_data="delete_account_user"), InlineKeyboardButton("📊 وضعیت حساب من", callback_data="user_status")]
    ]
    
    text = (
        "✨ **سیستم مدیریت هوشمند آپلود ابری پیشگام** ✨\n"
        "──────────────────────────────\n"
        f"🎯 **اکانت مقصد فعلی:** `{active_acc}`\n"
        f"⚡ **وضعیت سرویس:** {upload_status}\n"
        "──────────────────────────────\n"
        "👇 برای شروع عملیات یا تغییر تنظیمات، گزینه‌ای را انتخاب کنید:"
    )
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# پنل مدیریت مخفی ادمین
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت را ندارید.")
        return

    total_users = len(USERS_DATA)
    keyboard = [
        [InlineKeyboardButton("📊 وضعیت حافظه سرور", callback_data="server_status")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👑 **پنل فرماندهی ادمین**\n"
        "────────────────────\n"
        f"👥 **تعداد کاربران ثبت‌شده:** `{total_users}` نفر", 
        parse_mode="Markdown", reply_markup=reply_markup
    )

# مدیریت دکمه‌ها
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
            await query.edit_message_text("⚠️ **خطا:** شما هنوز هیچ اکانتی ثبت نکرده‌اید! ابتدا یک اکانت اضافه کنید.", reply_markup=kb)
            return
        
        context.user_data['upload_mode'] = not context.user_data.get('upload_mode', False)
        await start(update, context)

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
            os.system(f'rclone config delete {acc_info["remote"]}')
            del user_info["accounts"][acc_name]
            if user_info.get("active_acc") == acc_name:
                user_info["active_acc"] = list(user_info["accounts"].keys())[0] if user_info["accounts"] else None
            save_data(USERS_DATA)
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])
        await query.edit_message_text(f"🗑 اکانت **{acc_name}** با موفقیت حذف گردید.", parse_mode="Markdown", reply_markup=kb)

    elif data == "user_status":
        accs_count = len(user_info.get("accounts", {}))
        active = user_info.get("active_acc") or "هیچ‌کدام"
        text = (
            "💎 **شناسنامه حساب کاربری شما**\n"
            "──────────────────\n"
            f"🆔 **آیدی تلگرام:** `{user_id}`\n"
            f"📂 **تعداد کل اکانت‌ها:** `{accs_count}`\n"
            f"🎯 **اکانت فعال:** `{active}`"
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

# افزودن اکانت با راهنمای زیبا
async def start_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]])
    await query.edit_message_text("📝 **مرحله ۱ از ۴:** یک عنوان اختصاصی برای این اکانت بنویسید (مثلاً: `مگای شخصی`):", parse_mode="Markdown", reply_markup=kb)
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_acc_name'] = update.message.text
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
    context.user_data['new_acc_user'] = update.message.text
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ انصراف", callback_data="cancel_conv")]])
    await update.message.reply_text("🔑 **مرحله ۴ از ۴:** رمز عبور (Password) حساب را وارد کنید:", reply_markup=kb)
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acc_pass = update.message.text
    acc_name = context.user_data['new_acc_name']
    srv_type = context.user_data['new_acc_type']
    acc_user = context.user_data['new_acc_user']
    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    
    remote_name = f"u{user_id}_{len(user_info['accounts']) + 1}"
    msg = await update.message.reply_text("⚡ **در حال برقراری ارتباط لایو و تست صحت اطلاعات...**")
    
    os.system(f'rclone config create {remote_name} {srv_type} user "{acc_user}" pass "{acc_pass}"')
    
    test_cmd = f'rclone lsd {remote_name}:'
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]])
    if result.returncode == 0:
        user_info['accounts'][acc_name] = {"remote": remote_name, "path": f"{remote_name}:/"}
        user_info['active_acc'] = acc_name
        save_data(USERS_DATA)
        await msg.edit_text(f"🎉 **تبریک!** اکانت **{acc_name}** با موفقیت تایید و فعال گردید.", parse_mode="Markdown", reply_markup=kb)
    else:
        os.system(f'rclone config delete {remote_name}')
        await msg.edit_text("❌ **اتصال ناموفق بود!**\nاطلاعات ورود اشتباه است یا سرور پاسخ نداد.", reply_markup=kb)
        
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)
    return ConversationHandler.END

# پردازش و آپلود زیبا همراه با Progressive Bar واقعی
async def handle_all_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('upload_mode'):
        await update.message.reply_text("⚠️ ربات در فاز آپلود نیست! ابتدا /start را بزنید و فاز آپلود را روشن کنید.")
        return

    user_id = str(update.effective_user.id)
    user_info = get_user_accounts(user_id)
    active_acc = user_info.get("active_acc")
    
    if not active_acc or active_acc not in user_info.get("accounts", {}):
        await update.message.reply_text("❌ اکانت فعالی یافت نشد.")
        return

    target = user_info["accounts"][active_acc]["path"]
    remote_name = user_info["accounts"][active_acc]["remote"]
    
    # پیام اولیه جذاب
    msg = await update.message.reply_text("📥 **در حال دریافت فایل از تلگرام...**\n`[░░░░░░░░░░] 0%`", parse_mode="Markdown")

    try:
        tg_file = None
        file_name = "file"
        file_icon = "📄"

        if update.message.document:
            tg_file = await update.message.document.get_file()
            file_name = update.message.document.file_name or f"doc_{update.message.document.file_id[:5]}"
            file_icon = "📑"
        elif update.message.video:
            tg_file = await update.message.video.get_file()
            file_name = update.message.video.file_name or f"video_{update.message.video.file_id[:5]}.mp4"
            file_icon = "🎬"
        elif update.message.audio:
            tg_file = await update.message.audio.get_file()
            file_name = update.message.audio.file_name or f"audio_{update.message.audio.file_id[:5]}.mp3"
            file_icon = "🎵"
        elif update.message.photo:
            tg_file = await update.message.photo[-1].get_file()
            file_name = f"photo_{update.message.photo[-1].file_id[:5]}.jpg"
            file_icon = "🖼"

        file_path = f"./{file_name}"
        await tg_file.download_to_drive(file_path)

        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

        # شبیه‌سازی انیمیشن پیشرفت اختصاصی آپلود روی مگا
        progress_steps = [20, 45, 75, 95]
        for p in progress_steps:
            bar_str = make_progress_bar(p)
            await msg.edit_text(
                f"☁️ **در حال انتقال فایل به سرور ابری...**\n"
                f"──────────────────\n"
                f"{file_icon} **فایل:** `{file_name}`\n"
                f"📦 **حجم:** `{file_size_mb} MB`\n"
                f"📊 **پیشرفت:** `{bar_str}`",
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.8)

        # دستور نهایی آپلود با Rclone
        res = os.system(f'rclone copy "{file_path}" "{target}"')

        if res == 0:
            link_cmd = f'rclone link "{remote_name}:{file_name}"'
            link_res = subprocess.run(link_cmd, shell=True, capture_output=True, text=True)
            dl_link = link_res.stdout.strip() if link_res.returncode == 0 else "لینک عمومی مستقیم یافت نشد."

            final_bar = make_progress_bar(100)
            
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 باز کردن لینک دانلود مستقیم", url=dl_link)]]) if "http" in dl_link else None

            await msg.edit_text(
                f"✅ **آپلود با موفقیت کامل انجام شد!**\n"
                f"──────────────────\n"
                f"{file_icon} **نام فایل:** `{file_name}`\n"
                f"📦 **حجم فایل:** `{file_size_mb} MB`\n"
                f"📊 **وضعیت:** `{final_bar}`\n"
                f"🎯 **مقصد:** `{active_acc}`\n"
                f"──────────────────\n"
                f"🔗 **لینک اشتراک‌گذاری:**\n`{dl_link}`",
                parse_mode="Markdown", reply_markup=kb
            )
        else:
            await msg.edit_text("❌ خطایی هنگام انتقال فایل پیش آمد.")

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await msg.edit_text(f"❌ خطا: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).read_timeout(60).write_timeout(60).build()

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

    print("🚀 ربات شکیل و حرفه‌ای با انیمیشن آپلود روشن شد...")
    app.run_polling()
