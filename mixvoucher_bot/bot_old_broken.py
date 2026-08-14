import sqlite3
import logging
import json
import urllib.request
from datetime import datetime

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8349045061:AAFGST9D06RbOeB7PITxlS-_WgFKzr9AKlQ"
BOT_USERNAME = "@MixVoucher_bot"
ADMIN_ID = 5927935256

CARD_INFO = "شماره کارت: 0000-0000-0000-0000\nبه نام: نام صاحب کارت"
UVOUCHER_RATE = 65000
PROFIT_PERCENT = 8
NOBITEX_USDT_URL = "https://apiv2.nobitex.ir/v3/orderbook/USDTIRT"
DB_NAME = "mixvoucher.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def db():
    return sqlite3.connect(DB_NAME)


def is_admin(user_id: int):
    return user_id == ADMIN_ID


def normalize_phone(phone: str):
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        return "0" + phone[3:]
    if phone.startswith("98"):
        return "0" + phone[2:]
    return phone


def is_iranian_phone(phone: str):
    phone = normalize_phone(phone)
    return phone.startswith("09") and len(phone) == 11 and phone.isdigit()


def get_setting(key, default=""):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    con.close()
    return row[0] if row else default


def set_setting(key, value):
    con = db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    con.commit()
    con.close()


def get_profit_percent():
    try:
        return float(get_setting("profit_percent", str(PROFIT_PERCENT)))
    except Exception:
        return PROFIT_PERCENT


def get_card_info():
    return get_setting("card_info", CARD_INFO)


def get_fallback_rate():
    try:
        return int(float(get_setting("fallback_rate", str(UVOUCHER_RATE))))
    except Exception:
        return get_fallback_rate()


def get_usdt_rate_from_nobitex():
    try:
        req = urllib.request.Request(
            NOBITEX_USDT_URL,
            headers={"User-Agent": "MixVoucherBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "ok":
            raise ValueError("Nobitex status is not ok")

        price = int(float(data.get("lastTradePrice", 0)) / 10)
        if price <= 0:
            raise ValueError("Invalid USDT price")

        return price
    except Exception as e:
        logger.warning("Nobitex price fetch failed: %s", e)
        return get_fallback_rate()


def get_uvoucher_rate():
    usdt_rate = get_usdt_rate_from_nobitex()
    return int(usdt_rate * (1 + get_profit_percent() / 100))


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        wallet INTEGER DEFAULT 0,
        kyc_status TEXT DEFAULT 'not_started',
        is_blocked INTEGER DEFAULT 0,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount_usd REAL,
        price_irt INTEGER,
        status TEXT,
        receipt TEXT,
        voucher_code TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('profit_percent', ?)", (str(PROFIT_PERCENT),))
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_info', ?)", (CARD_INFO,))
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('fallback_rate', ?)", (str(UVOUCHER_RATE),))
    try:
        cur.execute("ALTER TABLE users ADD COLUMN user_level TEXT DEFAULT 'normal'")
    except sqlite3.OperationalError:
        pass

    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_limit_unverified', '500000')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_limit_normal', '5000000')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_limit_advanced', '20000000')")
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('daily_limit_pro', '0')")

    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('kyc_instruction', ?)", (
        "برای احراز هویت، لطفاً تصویر کارت ملی و یک سلفی واضح ارسال کنید.\n"
        "در سلفی، کارت ملی کنار صورت شما باشد.\n"
        "اطلاعات باید خوانا و تصویر بدون ادیت باشد.",
    ))

    con.commit()
    con.close()


def main_menu():
    return ReplyKeyboardMarkup([
        ["🛒 خرید Uvoucher"],
        ["👤 حساب کاربری", "💰 کیف پول"],
        ["📦 سفارشات من", "🎫 کدهای خریداری شده"],
        ["📞 پشتیبانی", "📖 راهنما"]
    ], resize_keyboard=True)


def phone_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📱 اشتراک شماره تلفن", request_contact=True)]
    ], resize_keyboard=True)


def get_user(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row


def user_has_phone(user_id):
    row = get_user(user_id)
    return bool(row and row[3])


def get_order(order_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, user_id, amount_usd, price_irt, status, receipt, voucher_code, created_at, updated_at
    FROM orders WHERE id=?
    """, (order_id,))
    row = cur.fetchone()
    con.close()
    return row


def order_status_fa(status):
    statuses = {
        "waiting_receipt": "در انتظار رسید",
        "waiting_admin": "در انتظار بررسی ادمین",
        "approved": "تأیید شده",
        "rejected": "رد شده",
        "delivered": "تحویل شده"
    }
    return statuses.get(status, status)


def order_detail_text(order):
    if not order:
        return "سفارش پیدا نشد."

    order_id, user_id, amount_usd, price_irt, status, receipt, voucher_code, created_at, updated_at = order

    return (
        f"📦 جزئیات سفارش #{order_id}\n\n"
        f"کاربر: {user_id}\n"
        f"مقدار: {amount_usd}$ Uvoucher\n"
        f"مبلغ: {price_irt:,} تومان\n"
        f"وضعیت: {order_status_fa(status)}\n"
        f"تاریخ ثبت: {created_at}\n"
        f"آخرین تغییر: {updated_at}\n"
        f"کد ووچر: {voucher_code or 'ثبت نشده'}"
    )


def order_admin_buttons(order_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{order_id}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_pending")]
    ])


def admin_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 سفارش‌های در انتظار", callback_data="admin_pending")],
        [InlineKeyboardButton("📦 آخرین سفارش‌ها", callback_data="admin_orders")],
        [InlineKeyboardButton("👥 کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📊 آمار", callback_data="admin_stats")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO users (user_id, username, full_name, joined_at) VALUES (?, ?, ?, ?)",
            (user.id, user.username or "", user.full_name or "", now())
        )
    else:
        cur.execute(
            "UPDATE users SET username=?, full_name=? WHERE user_id=?",
            (user.username or "", user.full_name or "", user.id)
        )

    con.commit()
    cur.execute("SELECT phone, is_blocked FROM users WHERE user_id=?", (user.id,))
    row = cur.fetchone()
    con.close()

    if row and row[1] == 1:
        await update.message.reply_text("حساب شما مسدود شده است.")
        return

    if not row or not row[0]:
        await update.message.reply_text(
            "سلام 👋\nبه ربات MixVoucher خوش اومدی.\n\n"
            "برای استفاده از ربات، اول باید شماره تلفن ایرانی خودت رو با دکمه زیر به اشتراک بذاری.",
            reply_markup=phone_menu()
        )
        return

    await update.message.reply_text("به منوی اصلی خوش اومدی 👇", reply_markup=main_menu())


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user

    if contact.user_id != user.id:
        await update.message.reply_text("لطفاً فقط شماره تلفن خودت رو ارسال کن.")
        return

    phone = normalize_phone(contact.phone_number)

    if not is_iranian_phone(phone):
        await update.message.reply_text(
            "فقط شماره‌های ایران مجاز هستند.\nلطفاً با شماره ایرانی وارد شوید.",
            reply_markup=phone_menu()
        )
        return

    con = db()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO users (user_id, username, full_name, phone, joined_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        phone=excluded.phone,
        username=excluded.username,
        full_name=excluded.full_name
    """, (user.id, user.username or "", user.full_name or "", phone, now()))
    con.commit()
    con.close()

    await update.message.reply_text(
        "شماره ایرانی شما با موفقیت ثبت شد ✅\nحالا می‌تونی از منوی اصلی استفاده کنی.",
        reply_markup=main_menu()
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی نداری.")
        return

    await update.message.reply_text("👨‍💼 پنل مدیریت MixVoucher", reply_markup=admin_home_keyboard())


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    row = get_user(user.id)

    if row and len(row) > 6 and row[6] == 1:
        await update.message.reply_text("حساب شما مسدود شده است.")
        return

    if not user_has_phone(user.id):
        await update.message.reply_text(
            "برای استفاده از ربات اول شماره تلفن ایرانی خودت رو ثبت کن.",
            reply_markup=phone_menu()
        )
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_profit":
        try:
            profit = float(text.strip())
            if profit < 0 or profit > 100:
                raise ValueError
        except ValueError:
            await update.message.reply_text("درصد سود نامعتبر است. مثال: 8")
            return

        set_setting("profit_percent", profit)
        context.user_data["admin_mode"] = None
        await update.message.reply_text(f"درصد سود روی {profit}% تنظیم شد ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_card":
        set_setting("card_info", text.strip())
        context.user_data["admin_mode"] = None
        await update.message.reply_text("اطلاعات کارت با موفقیت ذخیره شد ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_fallback_rate":
        try:
            rate = int(text.replace(",", "").strip())
            if rate <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("نرخ پشتیبان نامعتبر است. مثال: 170000")
            return

        set_setting("fallback_rate", rate)
        context.user_data["admin_mode"] = None
        await update.message.reply_text(f"نرخ پشتیبان روی {rate:,} تومان تنظیم شد ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_user_level":
        parts = text.strip().split()
        if len(parts) != 2 or parts[1] not in ["normal", "advanced", "pro"]:
            await update.message.reply_text("فرمت صحیح:\nUSER_ID normal\nUSER_ID advanced\nUSER_ID pro")
            return

        target_id = int(parts[0])
        level = parts[1]

        con = db()
        cur = con.cursor()
        cur.execute("UPDATE users SET user_level=? WHERE user_id=?", (level, target_id))
        con.commit()
        con.close()

        context.user_data["admin_mode"] = None
        await update.message.reply_text(f"سطح کاربر {target_id} به {level_fa(level)} تغییر کرد ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_limit":
        limit_key = context.user_data.get("limit_key")
        try:
            amount = int(text.replace(",", "").strip())
            if amount < 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("عدد نامعتبر است. مثال: 500000")
            return

        set_setting(limit_key, amount)
        context.user_data["admin_mode"] = None
        context.user_data["limit_key"] = None
        await update.message.reply_text(f"سقف جدید ذخیره شد: {amount:,} تومان ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "set_kyc_instruction":
        set_setting("kyc_instruction", text.strip())
        context.user_data["admin_mode"] = None
        await update.message.reply_text("روش احراز هویت با موفقیت بروزرسانی شد ✅")
        return

    if is_admin(user.id) and context.user_data.get("admin_mode") == "send_voucher":
        order_id = context.user_data.get("admin_order_id")
        voucher_code = text.strip()

        con = db()
        cur = con.cursor()
        cur.execute(
            "UPDATE orders SET voucher_code=?, status='delivered', updated_at=? WHERE id=?",
            (voucher_code, now(), order_id)
        )
        cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
        target = cur.fetchone()
        con.commit()
        con.close()

        context.user_data["admin_mode"] = None
        context.user_data["admin_order_id"] = None

        if target:
            await context.bot.send_message(
                chat_id=target[0],
                text=f"🎫 سفارش #{order_id} تکمیل شد ✅\n\nکد Uvoucher شما:\n\n`{voucher_code}`",
                parse_mode="Markdown"
            )

        await update.message.reply_text(f"کد برای سفارش #{order_id} ارسال شد ✅")
        return

    menu_buttons = [
        "🛒 خرید Uvoucher",
        "👤 حساب کاربری",
        "💰 کیف پول",
        "📦 سفارشات من",
        "🎫 کدهای خریداری شده",
        "📞 پشتیبانی",
        "📖 راهنما"
    ]

    mode = context.user_data.get("mode")

    if text in menu_buttons and mode in ["buy_amount", "waiting_receipt", "support"]:
        context.user_data["mode"] = None
        context.user_data["receipt_order_id"] = None
        mode = None

    if text == "🛒 خرید Uvoucher":
        context.user_data["mode"] = "buy_amount"
        await update.message.reply_text(
            "مبلغ Uvoucher موردنظر رو به دلار وارد کن.\n\nمثال:\n10\n25\n100"
        )
        return

    if mode == "buy_amount":
        try:
            amount = float(text.replace("$", "").strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("لطفاً فقط عدد معتبر وارد کن. مثال: 10")
            return

        rate = get_uvoucher_rate()
        price = int(amount * rate)

        limit = get_daily_limit(user.id)
        today_total = get_today_total(user.id)

        if limit != 0 and today_total + price > limit:
            await update.message.reply_text(
                f"❌ سقف خرید روزانه شما کافی نیست.\n\n"
                f"سقف روزانه: {limit:,} تومان\n"
                f"خرید امروز: {today_total:,} تومان\n"
                f"مبلغ این سفارش: {price:,} تومان\n\n"
                "برای افزایش سقف، احراز هویت یا ارتقای سطح کاربری لازم است."
            )
            return

        con = db()
        cur = con.cursor()
        cur.execute("""
        INSERT INTO orders (user_id, amount_usd, price_irt, status, created_at, updated_at)
        VALUES (?, ?, ?, 'waiting_receipt', ?, ?)
        """, (user.id, amount, price, now(), now()))
        order_id = cur.lastrowid
        con.commit()
        con.close()

        context.user_data["mode"] = "waiting_receipt"
        context.user_data["receipt_order_id"] = order_id

        await update.message.reply_text(
            f"✅ سفارش شما ثبت شد.\n\n"
            f"شماره سفارش: #{order_id}\n"
            f"مقدار: {amount}$ Uvoucher\n"
            f"نرخ هر دلار Uvoucher: {rate:,} تومان\n"
            f"مبلغ پرداختی: {price:,} تومان\n\n"
            f"{get_card_info()}\n\n"
            f"بعد از پرداخت، عکس رسید یا متن رسید رو همینجا ارسال کن.\n\n"
            f"برای لغو، یکی از دکمه‌های منو را بزن."
        )
        return

    if mode == "waiting_receipt":
        order_id = context.user_data.get("receipt_order_id")
        await save_receipt_and_notify_admin(update, context, order_id, text, is_photo=False)
        return

    if text == "👤 حساب کاربری":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT full_name, username, phone, wallet, kyc_status, joined_at, user_level
        FROM users WHERE user_id=?
        """, (user.id,))
        info = cur.fetchone()
        con.close()

        daily_limit = get_daily_limit(user.id)
        daily_limit_text = "نامحدود" if daily_limit == 0 else f"{daily_limit:,} تومان"

        msg = (
            "👤 حساب کاربری شما\n\n"
            f"نام: {info[0]}\n"
            f"یوزرنیم: @{info[1] if info[1] else 'ندارد'}\n"
            f"آیدی عددی: {user.id}\n"
            f"شماره موبایل: {info[2]}\n"
            f"کیف پول: {info[3]:,} تومان\n"
            f"احراز هویت: {kyc_fa(info[4])}\n"
            f"سطح کاربری: {level_fa(info[6])}\n"
            f"سقف خرید روزانه: {daily_limit_text}\n"
            f"خرید امروز: {get_today_total(user.id):,} تومان\n"
            f"تاریخ عضویت: {info[5]}"
        )

        await update.message.reply_text(msg, reply_markup=profile_keyboard())
        return

    if text == "💰 کیف پول":
        info = get_user(user.id)
        await update.message.reply_text(
            f"💰 کیف پول شما\n\n"
            f"موجودی: {info[4]:,} تومان\n\n"
            "شارژ کیف پول فعلاً به‌صورت دستی توسط ادمین انجام می‌شود."
        )
        return

    if text == "📦 سفارشات من":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, amount_usd, price_irt, status, created_at
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """, (user.id,))
        rows = cur.fetchall()
        con.close()

        if not rows:
            await update.message.reply_text("هنوز سفارشی ثبت نکردی.")
            return

        msg = "📦 سفارشات اخیر شما:\n\n"
        for r in rows:
            msg += (
                f"#{r[0]} | {r[1]}$ | {r[2]:,} تومان\n"
                f"وضعیت: {order_status_fa(r[3])}\n"
                f"تاریخ: {r[4]}\n\n"
            )

        await update.message.reply_text(msg)
        return

    if text == "🎫 کدهای خریداری شده":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, amount_usd, voucher_code, created_at
        FROM orders
        WHERE user_id=? AND status='delivered'
        ORDER BY id DESC
        """, (user.id,))
        rows = cur.fetchall()
        con.close()

        if not rows:
            await update.message.reply_text("هنوز کدی برای شما تحویل نشده.")
            return

        msg = "🎫 کدهای خریداری‌شده:\n\n"
        for r in rows:
            msg += f"سفارش #{r[0]} | {r[1]}$\n`{r[2]}`\n{r[3]}\n\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text == "📞 پشتیبانی":
        context.user_data["mode"] = "support"
        await update.message.reply_text("پیام خودت رو برای پشتیبانی ارسال کن.")
        return

    if mode == "support":
        context.user_data["mode"] = None
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📞 پیام پشتیبانی جدید\n\n"
                f"کاربر: {user.full_name}\n"
                f"آیدی عددی: {user.id}\n"
                f"یوزرنیم: @{user.username}\n\n"
                f"پیام:\n{text}"
            )
        )
        await update.message.reply_text("پیام شما برای پشتیبانی ارسال شد ✅")
        return

    if text == "📖 راهنما":
        await update.message.reply_text(
            "📖 راهنمای خرید Uvoucher\n\n"
            "1. گزینه خرید Uvoucher رو بزن.\n"
            "2. مبلغ دلاری موردنظر رو وارد کن.\n"
            "3. مبلغ ریالی و اطلاعات پرداخت نمایش داده میشه.\n"
            "4. رسید پرداخت رو ارسال کن.\n"
            "5. بعد از تأیید ادمین، کد Uvoucher برات ارسال میشه.\n\n"
            "برای استفاده از ربات، شماره تلفن ایرانی الزامی است."
        )
        return

    await update.message.reply_text("لطفاً از منوی پایین یکی از گزینه‌ها رو انتخاب کن.")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user_has_phone(user.id):
        await update.message.reply_text(
            "برای استفاده از ربات اول شماره تلفن ایرانی خودت رو ثبت کن.",
            reply_markup=phone_menu()
        )
        return

    if context.user_data.get("mode") != "waiting_receipt":
        await update.message.reply_text("عکس دریافت شد، اما سفارشی در انتظار رسید نداری.")
        return

    order_id = context.user_data.get("receipt_order_id")
    photo = update.message.photo[-1].file_id

    await save_receipt_and_notify_admin(update, context, order_id, photo, is_photo=True)


async def save_receipt_and_notify_admin(update, context, order_id, receipt, is_photo=False):
    user = update.effective_user

    con = db()
    cur = con.cursor()
    cur.execute("""
    UPDATE orders
    SET receipt=?, status='waiting_admin', updated_at=?
    WHERE id=?
    """, (receipt, now(), order_id))
    cur.execute("""
    SELECT amount_usd, price_irt
    FROM orders
    WHERE id=?
    """, (order_id,))
    order = cur.fetchone()
    con.commit()
    con.close()

    context.user_data["mode"] = None
    context.user_data["receipt_order_id"] = None

    await update.message.reply_text(
        f"رسید سفارش #{order_id} ثبت شد ✅\n"
        "سفارش شما در انتظار بررسی ادمین است."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{order_id}")],
        [InlineKeyboardButton("🔍 جزئیات", callback_data=f"order_{order_id}")]
    ])

    caption = (
        f"📥 سفارش جدید در انتظار بررسی\n\n"
        f"شماره سفارش: #{order_id}\n"
        f"کاربر: {user.full_name}\n"
        f"آیدی عددی: {user.id}\n"
        f"یوزرنیم: @{user.username}\n"
        f"مقدار: {order[0]}$ Uvoucher\n"
        f"مبلغ: {order[1]:,} تومان"
    )

    if is_photo:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=receipt,
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=caption + f"\n\nرسید متنی:\n{receipt}",
            reply_markup=keyboard
        )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "profile_kyc":
        await query.message.reply_text(
            "🪪 روش احراز هویت\n\n" + get_kyc_instruction()
        )
        return

    if data == "profile_orders":
        await query.message.reply_text("برای مشاهده سفارشات از دکمه 📦 سفارشات من استفاده کن.")
        return

    if not is_admin(query.from_user.id):
        await query.edit_message_text("دسترسی نداری.")
        return

    if data == "admin_home":
        await query.edit_message_text(
            "👨‍💼 پنل مدیریت MixVoucher",
            reply_markup=admin_home_keyboard()
        )
        return

    if data == "admin_pending":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, amount_usd, price_irt, status
        FROM orders
        WHERE status IN ('waiting_admin', 'approved')
        ORDER BY id DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "سفارش در انتظاری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
                ])
            )
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"#{r[0]} | {r[2]}$ | {order_status_fa(r[4])}",
                    callback_data=f"order_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")])

        await query.edit_message_text(
            "📥 سفارش‌های در انتظار:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data == "admin_orders":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, amount_usd, price_irt, status
        FROM orders
        ORDER BY id DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "هنوز سفارشی ثبت نشده.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
                ])
            )
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"#{r[0]} | {r[2]}$ | {order_status_fa(r[4])}",
                    callback_data=f"order_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")])

        await query.edit_message_text(
            "📦 آخرین سفارش‌ها:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("order_"):
        order_id = int(data.split("_")[1])
        order = get_order(order_id)

        await query.edit_message_text(
            order_detail_text(order),
            reply_markup=order_admin_buttons(order_id)
        )
        return

    if data == "admin_users":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT user_id, full_name, phone, wallet, kyc_status, is_blocked
        FROM users
        ORDER BY joined_at DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "کاربری ثبت نشده.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
                ])
            )
            return

        msg = "👥 آخرین کاربران:\n\n"
        for r in rows:
            block = "مسدود" if r[5] == 1 else "فعال"
            msg += (
                f"آیدی: {r[0]}\n"
                f"نام: {r[1]}\n"
                f"شماره: {r[2] or 'ثبت نشده'}\n"
                f"کیف پول: {r[3]:,} تومان\n"
                f"احراز: {r[4]}\n"
                f"وضعیت: {block}\n\n"
            )

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
            ])
        )
        return

    if data == "admin_settings":
        msg = (
            "⚙️ تنظیمات ربات\n\n"
            f"درصد سود فعلی: {get_profit_percent()}%\n"
            f"نرخ پشتیبان: {get_fallback_rate():,} تومان\n\n"
            f"اطلاعات کارت فعلی:\n{get_card_info()}"
        )

        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ تغییر درصد سود", callback_data="set_profit")],
                [InlineKeyboardButton("💳 تغییر کارت", callback_data="set_card")],
                [InlineKeyboardButton("💵 تغییر نرخ پشتیبان", callback_data="set_fallback_rate")],
                [InlineKeyboardButton("🪪 تنظیم روش احراز", callback_data="set_kyc_instruction")],
                [InlineKeyboardButton("⭐ سطح‌بندی کاربر", callback_data="admin_set_level")],
                [InlineKeyboardButton("🚧 سقف خرید روزانه", callback_data="admin_limits")],
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
            ])
        )
        return

    if data == "set_profit":
        context.user_data["admin_mode"] = "set_profit"
        await query.message.reply_text("درصد سود جدید را وارد کن. مثال: 8")
        return

    if data == "set_card":
        context.user_data["admin_mode"] = "set_card"
        await query.message.reply_text("اطلاعات کارت جدید را کامل ارسال کن.")
        return

    if data == "set_fallback_rate":
        context.user_data["admin_mode"] = "set_fallback_rate"
        await query.message.reply_text("نرخ پشتیبان هر دلار Uvoucher را به تومان وارد کن. مثال: 170000")
        return

    if data == "set_kyc_instruction":
        context.user_data["admin_mode"] = "set_kyc_instruction"
        await query.message.reply_text(
            "متن جدید روش احراز هویت را کامل ارسال کن.\n\n"
            f"متن فعلی:\n{get_kyc_instruction()}"
        )
        return

    if data == "admin_set_level":
        context.user_data["admin_mode"] = "set_user_level"
        await query.message.reply_text(
            "آیدی عددی کاربر و سطح جدید را ارسال کن.\n\n"
            "سطح‌ها:\n"
            "normal = معمولی\n"
            "advanced = پیشرفته\n"
            "pro = حرفه‌ای\n\n"
            "مثال:\n8540867266 advanced"
        )
        return

    if data == "admin_limits":
        await query.edit_message_text(
            "🚧 سقف خرید روزانه\n\n"
            f"احراز نشده: {int(get_setting('daily_limit_unverified', '500000')):,} تومان\n"
            f"معمولی: {int(get_setting('daily_limit_normal', '5000000')):,} تومان\n"
            f"پیشرفته: {int(get_setting('daily_limit_advanced', '20000000')):,} تومان\n"
            f"حرفه‌ای: {'نامحدود' if int(get_setting('daily_limit_pro', '0')) == 0 else f'{int(get_setting('daily_limit_pro', '0')):,} تومان'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("احراز نشده", callback_data="limit_daily_limit_unverified")],
                [InlineKeyboardButton("معمولی", callback_data="limit_daily_limit_normal")],
                [InlineKeyboardButton("پیشرفته", callback_data="limit_daily_limit_advanced")],
                [InlineKeyboardButton("حرفه‌ای", callback_data="limit_daily_limit_pro")],
                [InlineKeyboardButton("🔙 تنظیمات", callback_data="admin_settings")]
            ])
        )
        return

    if data.startswith("limit_"):
        key = data.replace("limit_", "")
        context.user_data["admin_mode"] = "set_limit"
        context.user_data["limit_key"] = key
        await query.message.reply_text("سقف جدید را به تومان وارد کن. برای نامحدود عدد 0 بفرست.")
        return

    if data == "admin_stats":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='delivered'")
        delivered_count = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(price_irt), 0) FROM orders WHERE status='delivered'")
        total_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='waiting_admin'")
        pending_count = cur.fetchone()[0]
        con.close()

        await query.edit_message_text(
            f"📊 آمار ربات\n\n"
            f"کاربران: {users_count}\n"
            f"کل سفارش‌ها: {orders_count}\n"
            f"در انتظار بررسی: {pending_count}\n"
            f"تحویل‌شده: {delivered_count}\n"
            f"فروش کل تحویل‌شده: {total_sales:,} تومان",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
            ])
        )
        return

    action_parts = data.split("_")

    if len(action_parts) == 2:
        action = action_parts[0]
        order_id = int(action_parts[1])

        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
        row = cur.fetchone()

        if not row:
            con.close()
            await query.edit_message_text("سفارش پیدا نشد.")
            return

        target_user = row[0]

        if action == "approve":
            cur.execute(
                "UPDATE orders SET status='approved', updated_at=? WHERE id=?",
                (now(), order_id)
            )
            con.commit()
            con.close()

            await context.bot.send_message(
                chat_id=target_user,
                text=f"✅ سفارش #{order_id} تأیید شد.\nدر انتظار ارسال کد Uvoucher باشید."
            )

            await query.edit_message_text(
                f"سفارش #{order_id} تأیید شد ✅",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{order_id}")],
                    [InlineKeyboardButton("🔙 سفارش‌های در انتظار", callback_data="admin_pending")]
                ])
            )
            return

        if action == "reject":
            cur.execute(
                "UPDATE orders SET status='rejected', updated_at=? WHERE id=?",
                (now(), order_id)
            )
            con.commit()
            con.close()

            await context.bot.send_message(
                chat_id=target_user,
                text=f"❌ سفارش #{order_id} رد شد.\nبرای پیگیری با پشتیبانی ارتباط بگیر."
            )

            await query.edit_message_text(
                f"سفارش #{order_id} رد شد ❌",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 سفارش‌های در انتظار", callback_data="admin_pending")]
                ])
            )
            return

        if action == "deliver":
            con.close()
            context.user_data["admin_mode"] = "send_voucher"
            context.user_data["admin_order_id"] = order_id

            await query.message.reply_text(
                f"کد Uvoucher سفارش #{order_id} رو همینجا ارسال کن."
            )
            return


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("MixVoucher Bot V2 is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
