


import sqlite3
import secrets
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

DB_NAME = "mixvoucher.db"

NOBITEX_USDT_URL = "https://apiv2.nobitex.ir/v3/orderbook/USDTIRT"

DEFAULT_PROFIT_PERCENT = 8
DEFAULT_FALLBACK_RATE = 170000

DEFAULT_CARD_INFO = """شماره کارت: 0000-0000-0000-0000
به نام: نام صاحب کارت"""
KYC_SAMPLE_IMAGE_PATH = "assets/kyc_sample.png"

DEFAULT_KYC_TEXT = """اینجانب [نام و نام خانوادگی] با کد ملی [کد ملی] و شماره موبایل [شماره موبایل] و ایمیل [ایمیل] درخواست احراز هویت در ربات MixVoucher را دارم.
متعهد می‌شوم اطلاعات واردشده متعلق به خودم بوده و مسئولیت استفاده از حساب کاربری بر عهده من است.
این احراز صرفاً جهت خرید و استفاده از خدمات ربات MixVoucher انجام می‌شود.
هرگونه سوءاستفاده از اطلاعات یا خرید با مشخصات غیرواقعی بر عهده کاربر است.
با قوانین و شرایط استفاده از خدمات MixVoucher موافقم.

تاریخ:
امضا:
نام و نام خانوادگی:"""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return datetime.now().strftime("%Y-%m-%d")


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


def kyc_fa(status):
    return {
        "not_started": "احراز نشده",
        "pending": "در انتظار بررسی",
        "verified": "تأیید شده",
        "rejected": "رد شده",
    }.get(status or "not_started", "احراز نشده")


def level_fa(level):
    return {
        "normal": "معمولی",
        "advanced": "پیشرفته",
        "pro": "حرفه‌ای",
    }.get(level or "normal", "معمولی")


def order_status_fa(status):
    return {
        "waiting_receipt": "در انتظار رسید",
        "waiting_admin": "در انتظار بررسی ادمین",
        "approved": "تأیید شده",
        "rejected": "رد شده",
        "delivered": "تحویل شده",
    }.get(status, status)


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
        user_level TEXT DEFAULT 'normal',
        is_blocked INTEGER DEFAULT 0,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount_usd REAL,
        rate INTEGER,
        price_toman INTEGER,
        status TEXT,
        receipt TEXT,
        reject_reason TEXT,
        voucher_code TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kyc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        image_file_id TEXT,
        status TEXT DEFAULT 'pending',
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

    defaults = {
        "profit_percent": str(DEFAULT_PROFIT_PERCENT),
        "fallback_rate": str(DEFAULT_FALLBACK_RATE),
        "card_info": DEFAULT_CARD_INFO,
        "kyc_text": DEFAULT_KYC_TEXT,
        "limit_unverified": "500000",
        "limit_normal": "5000000",
        "limit_advanced": "20000000",
        "limit_pro": "0",
        "kyc_text": DEFAULT_KYC_TEXT,
        "limit_unverified": "500000",
        "limit_normal": "3000000",
        "limit_advanced": "20000000",
        "limit_pro": "0",
    }

    for key, value in defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )

    con.commit()
    con.close()






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
        "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    con.commit()
    con.close()


def get_user(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row


def has_phone(user_id):
    row = get_user(user_id)
    return bool(row and row[3])


def get_rate():
    try:
        req = urllib.request.Request(
            NOBITEX_USDT_URL,
            headers={"User-Agent": "MixVoucherBot"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())

        usdt = int(float(data["lastTradePrice"]) / 10)
    except Exception:
        usdt = int(get_setting("fallback_rate", DEFAULT_FALLBACK_RATE))

    profit = float(get_setting("profit_percent", DEFAULT_PROFIT_PERCENT))
    return int(usdt * (1 + profit / 100))


def phone_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📱 اشتراک شماره تلفن", request_contact=True)]
    ], resize_keyboard=True)


def main_menu():
    return ReplyKeyboardMarkup([
        ["🛒 خرید Uvoucher"],
        ["👤 حساب کاربری", "💰 کیف پول"],
        ["📦 سفارشات من", "🎫 کدهای خریداری شده"],
        ["🏦 حساب‌های بانکی"],
        ["📞 پشتیبانی", "📖 راهنما"],
    ], resize_keyboard=True)


def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 سفارش‌های در انتظار", callback_data="admin_pending")],
        [InlineKeyboardButton("📦 آخرین سفارش‌ها", callback_data="admin_orders")],
        [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("🪪 احرازهای در انتظار", callback_data="admin_kyc")],
        [InlineKeyboardButton("🏦 حساب‌های بانکی", callback_data="admin_banks")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")],
    ])


def display_uid(user_id):
    uid = ensure_user_uid(user_id)
    return str(uid).replace("UID-", "")


def generate_uid(cur):
    for _ in range(100):
        uid = f"UID-{secrets.randbelow(90000) + 10000}"
        cur.execute("SELECT user_id FROM users WHERE uid=?", (uid,))
        if not cur.fetchone():
            return uid
    raise RuntimeError("Could not generate unique UID")


def ensure_user_uid(user_id):
    try:
        con = db()
        cur = con.cursor()

        try:
            cur.execute("ALTER TABLE users ADD COLUMN uid TEXT")
            con.commit()
        except sqlite3.OperationalError:
            pass

        cur.execute("SELECT uid FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()

        if not row:
            con.close()
            return "UID-ERROR"

        if row[0]:
            con.close()
            return row[0]

        uid = generate_uid(cur)
        cur.execute("UPDATE users SET uid=? WHERE user_id=?", (uid, user_id))
        con.commit()
        con.close()
        return uid

    except Exception as e:
        print("UID ERROR:", repr(e))
        return "UID-ERROR"


def make_order_number(product_type, order_id, created_at=None):
    return f"{product_type}-{int(order_id):06d}"


def make_tracking_code(length=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(length))
    return raw[:3] + "-" + raw[3:]


def tracking_exists(code):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id FROM orders WHERE tracking_code=?", (code,))
    row = cur.fetchone()
    con.close()
    return bool(row)


def generate_unique_tracking_code():
    for _ in range(50):
        code = make_tracking_code()
        if not tracking_exists(code):
            return code
    raise RuntimeError("Could not generate unique tracking code")


def ensure_order_identity(order_id, product_type="UV"):
    try:
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, order_number, tracking_code, product_type, created_at
        FROM orders
        WHERE id=?
        """, (order_id,))
        row = cur.fetchone()

        if not row:
            con.close()
            print("IDENTITY ERROR: order not found", order_id)
            return f"#{order_id}", "-"

        oid, order_number, tracking_code, current_product, created_at = row
        product = current_product or product_type

        if not order_number:
            order_number = make_order_number(product, oid, created_at)

        if not tracking_code:
            alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
            for _ in range(100):
                code = "".join(secrets.choice(alphabet) for _ in range(6))
                cur.execute("SELECT id FROM orders WHERE tracking_code=? AND id!=?", (code, oid))
                if not cur.fetchone():
                    tracking_code = code
                    break

        cur.execute(
            "UPDATE orders SET order_number=?, tracking_code=?, product_type=? WHERE id=?",
            (order_number, tracking_code, product, oid)
        )
        con.commit()
        con.close()

        print("IDENTITY OK:", order_id, order_number, tracking_code)
        return order_number, tracking_code

    except Exception as e:
        print("IDENTITY EXCEPTION:", repr(e))
        return f"#{order_id}", "-"


def get_today_total(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT COALESCE(SUM(price_toman), 0)
    FROM orders
    WHERE user_id=? AND status != 'rejected' AND substr(created_at, 1, 10)=?
    """, (user_id, datetime.now().strftime("%Y-%m-%d")))
    total = cur.fetchone()[0]
    con.close()
    return int(total or 0)


def get_daily_limit(row):
    if not row:
        return 500000

    kyc_status = row[5]
    level = row[6]

    if kyc_status != "verified":
        return int(get_setting("limit_unverified", "500000"))

    if level == "advanced":
        return int(get_setting("limit_advanced", "20000000"))

    if level == "pro":
        return int(get_setting("limit_pro", "0"))

    return int(get_setting("limit_normal", "3000000"))


def limit_text(amount):
    return "نامحدود" if int(amount) == 0 else f"{int(amount):,} تومان"


def format_order_code(order_id, created_at=None):
    date_part = datetime.now().strftime("%Y%m%d")
    if created_at:
        date_part = str(created_at)[:10].replace("-", "")
    return f"MV-{date_part}-{int(order_id):06d}"


def get_total_purchase(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT COALESCE(SUM(price_toman), 0)
    FROM orders
    WHERE user_id=? AND status='delivered'
    """, (user_id,))
    total = cur.fetchone()[0]
    con.close()
    return int(total or 0)


def admin_user_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 سفارشات کاربر", callback_data=f"admin_user_orders_{user_id}")],
        [InlineKeyboardButton("⭐ تغییر سطح", callback_data=f"admin_user_level_{user_id}")],
        [InlineKeyboardButton("🪪 تغییر احراز", callback_data=f"admin_user_kyc_{user_id}")],
        [InlineKeyboardButton("🚫 مسدود/آزاد", callback_data=f"admin_user_block_{user_id}")],
        [InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")]
    ])


def admin_user_text(row):
    daily_limit = get_daily_limit(row)
    today_total = get_today_total(row[0])
    total_purchase = get_total_purchase(row[0])
    block_status = "مسدود" if row[7] == 1 else "فعال"

    return (
        "👤 پروفایل کاربر\n\n"
        f"👤 نام: {row[2]}\n"
        f"🔗 یوزرنیم: @{row[1] if row[1] else 'ندارد'}\n"
        f"🆔 شناسه کاربری: {display_uid(row[0])}\n"
        f"تلگرام: {row[0]}\n"
        f"📱 شماره: {row[3]}\n"
        f"💰 کیف پول: {row[4]:,} تومان\n"
        f"🪪 احراز: {kyc_fa(row[5])}\n"
        f"⭐ سطح: {level_fa(row[6])}\n"
        f"🚧 سقف روزانه: {limit_text(daily_limit)}\n"
        f"📊 خرید امروز: {today_total:,} تومان\n"
        f"📊 مجموع خرید موفق: {total_purchase:,} تومان\n"
        f"🚦 وضعیت: {block_status}\n"
        f"📅 عضویت: {row[8]}"
    )


def normalize_digits(text):
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return str(text).translate(table)


def normalize_sheba(text):
    text = normalize_digits(text).upper()
    text = text.replace(" ", "").replace("-", "").replace("_", "")
    text = text.replace("‌", "").replace("\u200c", "")
    return text


def bank_display_name(bank_name, card):
    card = str(card).replace(" ", "").replace("-", "")
    last4 = card[-4:] if len(card) >= 4 else card
    return f"{bank_name or 'در انتظار بررسی'} {last4}"


def mask_card(card):
    card = str(card).replace(" ", "").replace("-", "")
    if len(card) < 10:
        return card
    return f"{card[:4]}-****-****-{card[-4:]}"


def bank_accounts_keyboard(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, card_number, bank_name, status
    FROM bank_accounts
    WHERE user_id=?
    ORDER BY id DESC
    """, (user_id,))
    rows = cur.fetchall()
    con.close()

    buttons = []
    for r in rows:
        bank = r[2] or "در انتظار بررسی"
        status = "✅" if r[3] == "approved" else "⏳" if r[3] == "pending" else "❌"
        buttons.append([
            InlineKeyboardButton(
                f"{status} {bank_display_name(bank, r[1])}",
                callback_data="noop"
            )
        ])

    buttons.append([InlineKeyboardButton("➕ افزودن حساب بانکی جدید", callback_data="bank_add")])
    buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def wallet_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزایش موجودی", callback_data="wallet_deposit")],
        [InlineKeyboardButton("💸 درخواست برداشت", callback_data="wallet_withdraw")],
        [InlineKeyboardButton("📜 تاریخچه تراکنش‌ها", callback_data="wallet_history")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
    ])


def profile_keyboard(row):
    daily_limit = get_daily_limit(row)
    today_total = get_today_total(row[0])
    remaining = 0 if daily_limit != 0 and today_total >= daily_limit else daily_limit - today_total if daily_limit != 0 else 0

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"👤 نام: {row[2]}", callback_data="noop")],
        [InlineKeyboardButton(f"🔗 یوزرنیم: @{row[1] if row[1] else 'ندارد'}", callback_data="noop")],
        [InlineKeyboardButton(f"🆔 شناسه کاربری: {display_uid(row[0])}", callback_data="noop")],
        [InlineKeyboardButton(f"تلگرام: {row[0]}", callback_data="noop")],
        [InlineKeyboardButton(f"📱 شماره: {row[3]}", callback_data="noop")],
        [InlineKeyboardButton(f"💰 کیف پول: {row[4]:,} تومان", callback_data="noop")],
        [InlineKeyboardButton(f"🪪 احراز: {kyc_fa(row[5])}", callback_data="user_kyc")],
        [InlineKeyboardButton(f"⭐ سطح: {level_fa(row[6])}", callback_data="noop")],
        [InlineKeyboardButton(f"💳 سقف روزانه: {limit_text(daily_limit)}", callback_data="noop")],
        [InlineKeyboardButton(f"📊 خرید امروز: {today_total:,} تومان", callback_data="noop")],
        [InlineKeyboardButton(f"✅ باقیمانده امروز: {'نامحدود' if daily_limit == 0 else f'{remaining:,} تومان'}", callback_data="noop")],
        [InlineKeyboardButton("📦 سفارشات من", callback_data="user_orders")],
    ])


def order_status_icon(status):
    if status == "delivered":
        return "✅"
    if status == "rejected":
        return "❌"
    return "⏳"


def order_status_text(status):
    names = {
        "waiting_receipt": "در انتظار رسید",
        "waiting_admin": "در انتظار بررسی",
        "approved": "تأیید شده",
        "delivered": "تحویل شده",
        "rejected": "رد شده",
    }
    return names.get(status, status)


def product_name(code):
    return {
        "UV": "Uvoucher",
        "HV": "Hot Voucher",
        "PV": "Premium Voucher",
    }.get(code or "UV", code or "Uvoucher")


def order_progress_text(status):
    if status == "waiting_receipt":
        return "✅ سفارش ثبت شد\n⬜ رسید پرداخت ثبت نشده\n⬜ بررسی مدیریت\n⬜ تحویل ووچر"
    if status == "waiting_admin":
        return "✅ سفارش ثبت شد\n✅ رسید پرداخت ثبت شد\n⏳ در انتظار بررسی مدیریت\n⬜ تحویل ووچر"
    if status == "approved":
        return "✅ سفارش ثبت شد\n✅ رسید پرداخت ثبت شد\n✅ تأیید مدیریت\n⏳ در انتظار تحویل ووچر"
    if status == "delivered":
        return "✅ سفارش ثبت شد\n✅ رسید پرداخت ثبت شد\n✅ تأیید مدیریت\n🎉 ووچر تحویل شد"
    if status == "rejected":
        return "✅ سفارش ثبت شد\n✅ رسید پرداخت ثبت شد\n❌ سفارش رد شد\n⬜ تحویل ووچر"
    return "—"


def order_detail_text(order_id, user_id):
    ensure_order_identity(order_id, "UV")

    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, amount_usd, price_toman, status, created_at, updated_at,
           order_number, tracking_code, product_type, completed_at, voucher_code
    FROM orders
    WHERE id=? AND user_id=?
    """, (order_id, user_id))
    o = cur.fetchone()
    con.close()

    if not o:
        return "سفارش پیدا نشد."

    oid, amount, price, status, created_at, updated_at, order_number, tracking_code, product_type, completed_at, voucher_code = o

    delivered_at = completed_at or "—"
    voucher = voucher_code if voucher_code else "هنوز ارسال نشده است."

    return (
        "📦 جزئیات سفارش\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"🆔 شماره سفارش\n{order_number}\n\n"
        f"🔎 کد رهگیری\n{tracking_code}\n\n"
        f"🎫 محصول\n{product_name(product_type)}\n\n"
        f"💵 مقدار\n{amount}$\n\n"
        f"💰 مبلغ پرداختی\n{price:,} تومان\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"📌 وضعیت\n{order_status_icon(status)} {order_status_text(status)}\n\n"
        f"📅 تاریخ ثبت\n{created_at}\n\n"
        f"📦 تاریخ تحویل\n{delivered_at}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"🧭 روند سفارش\n{order_progress_text(status)}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"🎁 کد ووچر\n{voucher}"
    )


def user_orders_inline_keyboard(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, amount_usd, price_toman, status, created_at, order_number, product_type
    FROM orders
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 20
    """, (user_id,))
    rows = cur.fetchall()
    con.close()

    buttons = []

    for r in rows:
        oid, amount, price, status, created_at, order_number, product_type = r
        identity = ensure_order_identity(oid, product_type or "UV")
        if identity:
            order_number = identity[0]

        buttons.append([
            InlineKeyboardButton(
                f"{order_status_icon(status)} {product_type or 'UV'} | {amount}$ | {order_number}",
                callback_data=f"user_order_view_{oid}"
            )
        ])

    buttons.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)


def user_order_detail_keyboard(order_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی وضعیت", callback_data=f"user_order_view_{order_id}")],
        [InlineKeyboardButton("🧾 مشاهده رسید پرداخت", callback_data=f"user_order_receipt_{order_id}")],
        [InlineKeyboardButton("📞 پشتیبانی", callback_data="user_support")],
        [InlineKeyboardButton("🔙 بازگشت به سفارشات", callback_data="user_orders")]
    ])


def flow_nav_keyboard(prev_callback="back_main"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 مرحله قبل", callback_data=prev_callback),
            InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")
        ]
    ])


def back_to_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
    ])


def buy_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_main")]
    ])


def receipt_method_keyboard(order_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 ارسال تصویر رسید تراکنش", callback_data=f"receipt_photo_{order_id}")],
        [InlineKeyboardButton("📝 ارسال متن رسید تراکنش", callback_data=f"receipt_text_{order_id}")],
        [
            InlineKeyboardButton("🔙 مرحله قبل", callback_data="back_buy_amount"),
            InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")
        ]
    ])


def user_orders_keyboard(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, amount_usd, price_toman, status
    FROM orders
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (user_id,))
    rows = cur.fetchall()
    con.close()

    buttons = []
    for r in rows:
        buttons.append([
            InlineKeyboardButton(
                f"#{r[0]} | {r[1]}$ | {order_status_fa(r[3])}",
                callback_data=f"user_order_{r[0]}"
            )
        ])

    buttons.append([InlineKeyboardButton("🔙 حساب کاربری", callback_data="user_profile")])
    return InlineKeyboardMarkup(buttons)


def user_orders_keyboard(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, amount_usd, price_toman, status
    FROM orders
    WHERE user_id=?
    ORDER BY id DESC
    LIMIT 10
    """, (user_id,))
    rows = cur.fetchall()
    con.close()

    buttons = []
    for r in rows:
        buttons.append([
            InlineKeyboardButton(
                f"#{r[0]} | {r[1]}$ | {order_status_fa(r[3])}",
                callback_data=f"user_order_{r[0]}"
            )
        ])

    buttons.append([InlineKeyboardButton("🔙 حساب کاربری", callback_data="user_profile")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            "INSERT INTO users(user_id, username, full_name, joined_at) VALUES(?,?,?,?)",
            (user.id, user.username or "", user.full_name or "", now())
        )
    else:
        cur.execute(
            "UPDATE users SET username=?, full_name=? WHERE user_id=?",
            (user.username or "", user.full_name or "", user.id)
        )

    con.commit()
    con.close()

    if not has_phone(user.id):
        await update.message.reply_text(
            "سلام 👋\nبرای استفاده از ربات، شماره ایرانی خودت رو با دکمه زیر ارسال کن.",
            reply_markup=phone_menu()
        )
        return

    context.user_data.clear()
    await update.message.reply_text("به منوی اصلی خوش اومدی 👇", reply_markup=main_menu())


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    contact = update.message.contact

    if contact.user_id != user.id:
        await update.message.reply_text("فقط شماره خودت رو ارسال کن.")
        return

    phone = normalize_phone(contact.phone_number)

    if not is_iranian_phone(phone):
        await update.message.reply_text("فقط شماره ایران مجاز است.", reply_markup=phone_menu())
        return

    con = db()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO users(user_id, username, full_name, phone, joined_at)
    VALUES(?,?,?,?,?)
    ON CONFLICT(user_id) DO UPDATE SET
        phone=excluded.phone,
        username=excluded.username,
        full_name=excluded.full_name
    """, (user.id, user.username or "", user.full_name or "", phone, now()))
    con.commit()
    con.close()

    ensure_user_uid(user.id)

    context.user_data.clear()
    await update.message.reply_text("شماره ثبت شد ✅", reply_markup=main_menu())


async def save_receipt(update, context, order_id, receipt, is_photo):
    user = update.effective_user

    con = db()
    cur = con.cursor()
    cur.execute(
        "UPDATE orders SET receipt=?, status='waiting_admin', updated_at=? WHERE id=?",
        (receipt, now(), order_id)
    )
    cur.execute("SELECT amount_usd, price_toman, order_number, tracking_code FROM orders WHERE id=?", (order_id,))
    order = cur.fetchone()
    con.commit()
    con.close()

    identity = ensure_order_identity(order_id, "UV")
    order_number, tracking_code = identity if identity else (f"#{order_id}", "-")

    context.user_data.clear()

    await update.message.reply_text(
        f"رسید سفارش {order_number} ثبت شد ✅\n"
        f"کد رهگیری: {tracking_code}\n"
        "در انتظار بررسی ادمین."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
        ],
        [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{order_id}")]
    ])

    caption = (
        f"📥 سفارش جدید\n\n"
        f"سفارش: {order_number}\n"
        f"کد رهگیری: {tracking_code}\n"
        f"کاربر: {user.full_name}\n"
        f"آیدی: {user.id}\n"
        f"یوزرنیم: @{user.username}\n"
        f"مقدار: {order[0]}$\n"
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
            text=caption + f"\n\nرسید:\n{receipt}",
            reply_markup=keyboard
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    row = get_user(user.id)
    if row and int(row[7]) == 1:
        await update.message.reply_text("حساب شما مسدود شده است.")
        return

    if not has_phone(user.id):
        await update.message.reply_text("اول شماره ایرانی خودت رو ثبت کن.", reply_markup=phone_menu())
        return

    menu_buttons = [
        "🛒 خرید Uvoucher",
        "👤 حساب کاربری",
        "💰 کیف پول",
        "📦 سفارشات من",
        "🎫 کدهای خریداری شده",
        "📞 پشتیبانی",
        "📖 راهنما",
    ]

    mode = context.user_data.get("mode")

    if mode == "kyc_upload":
        await update.message.reply_text(
            "🪪 شما در مرحله احراز هویت هستید.\n\n"
            "لطفاً تصویر احراز را ارسال کنید یا با دکمه زیر به منوی اصلی برگردید.",
            reply_markup=back_to_main_keyboard()
        )
        return

    if text in menu_buttons and mode in ["buy_amount", "receipt_choice", "waiting_receipt_photo", "waiting_receipt_text", "waiting_tracking_code", "kyc_upload"]:
        if mode == "kyc_upload":
            await update.message.reply_text(
                "🪪 شما در مرحله احراز هویت هستید.\nلطفاً تصویر احراز را ارسال کن یا با دکمه زیر خارج شو.",
                reply_markup=back_to_main_keyboard()
            )
            return

        if mode == "buy_amount":
            await update.message.reply_text(
                "🛒 شما در مرحله وارد کردن مبلغ خرید هستید.\n\n"
                "لطفاً مبلغ دلاری موردنظر را وارد کرده یا از دکمه زیر استفاده کنید.",
                reply_markup=buy_start_keyboard()
            )
            return

        order_id = context.user_data.get("order_id")
        await update.message.reply_text(
            "💳 شما در مرحله ارسال اطلاعات واریز هستید.\n"
            "لطفاً از دکمه‌های شیشه‌ای همان پیام استفاده کن.",
            reply_markup=receipt_method_keyboard(order_id) if order_id else back_to_main_keyboard()
        )
        return

    if text in menu_buttons and mode == "support":
        context.user_data.clear()
        mode = None

    if user.id == ADMIN_ID:
        admin_mode = context.user_data.get("admin_mode")

        if admin_mode == "kyc_reject_reason":
            kyc_id = context.user_data.get("kyc_id")
            target_user = context.user_data.get("target_user")
            reason = text.strip()

            con = db()
            cur = con.cursor()
            cur.execute(
                "UPDATE kyc_requests SET status='rejected', updated_at=? WHERE id=?",
                (now(), kyc_id)
            )
            cur.execute(
                "UPDATE users SET kyc_status='rejected' WHERE user_id=?",
                (target_user,)
            )
            con.commit()
            con.close()

            context.user_data.clear()

            await context.bot.send_message(
                chat_id=target_user,
                text=f"❌ احراز هویت شما رد شد.\n\nدلیل رد:\n{reason}"
            )
            await update.message.reply_text("دلیل رد احراز ارسال شد ✅")
            return

        if admin_mode == "order_reject_reason":
            order_id = context.user_data.get("order_id")
            reason = text.strip()

            if not order_id:
                context.user_data.clear()
                await update.message.reply_text("خطا: سفارش انتخاب نشده است.")
                return

            if not reason:
                await update.message.reply_text("لطفاً دلیل رد سفارش را وارد کن.")
                return

            con = db()
            cur = con.cursor()
            cur.execute(
                "UPDATE orders SET status='rejected', reject_reason=?, updated_at=? WHERE id=?",
                (reason, now(), order_id)
            )
            cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
            row = cur.fetchone()
            con.commit()
            con.close()

            context.user_data.clear()

            order_number = ensure_order_identity(order_id, "UV")[0]

            if row:
                await context.bot.send_message(
                    chat_id=row[0],
                    text=f"❌ سفارش {order_number} رد شد.\n\n📝 دلیل رد:\n{reason}"
                )

            await update.message.reply_text("دلیل رد سفارش برای کاربر ارسال شد ✅")
            return

        if admin_mode == "bank_set_name":
            bank_id = context.user_data.get("bank_id")
            bank_name = text.strip()

            con = db()
            cur = con.cursor()
            cur.execute("UPDATE bank_accounts SET bank_name=?, status='approved', updated_at=? WHERE id=?", (bank_name, now(), bank_id))
            cur.execute("SELECT user_id, card_number FROM bank_accounts WHERE id=?", (bank_id,))
            row = cur.fetchone()
            con.commit()
            con.close()

            context.user_data.clear()

            if row:
                await context.bot.send_message(
                    chat_id=row[0],
                    text=f"✅ حساب بانکی شما تأیید شد.\n{bank_display_name(bank_name, row[1])}"
                )

            await update.message.reply_text("حساب بانکی تأیید شد ✅")
            return

        if admin_mode == "bank_reject_reason":
            bank_id = context.user_data.get("bank_id")
            reason = text.strip()

            con = db()
            cur = con.cursor()
            cur.execute("UPDATE bank_accounts SET status='rejected', updated_at=? WHERE id=?", (now(), bank_id))
            cur.execute("SELECT user_id FROM bank_accounts WHERE id=?", (bank_id,))
            row = cur.fetchone()
            con.commit()
            con.close()

            context.user_data.clear()

            if row:
                await context.bot.send_message(
                    chat_id=row[0],
                    text=f"❌ حساب بانکی شما رد شد.\n\nدلیل رد:\n{reason}"
                )

            await update.message.reply_text("دلیل رد برای کاربر ارسال شد ✅")
            return

        if admin_mode == "admin_search":
            q = text.strip().replace("@", "")
            context.user_data.clear()

            # Order search: MV-YYYYMMDD-000123 or #123
            if q.upper().startswith("MV-") or q.startswith("#"):
                digits = "".join(ch for ch in q if ch.isdigit())
                order_id = int(digits[-6:]) if len(digits) >= 6 else int(digits)
                await send_admin_order_from_text(update, context, order_id)
                return

            # Pure number: try order first if short, then user
            if q.isdigit():
                num = int(q)
                if num < 1000000:
                    found = await send_admin_order_from_text(update, context, num, silent=True)
                    if found:
                        return

                row = get_user(num)
                if row:
                    await update.message.reply_text(admin_user_text(row), reply_markup=admin_user_keyboard(row[0]))
                    return

            # Phone / username / name search
            con = db()
            cur = con.cursor()
            cur.execute("""
            SELECT * FROM users
            WHERE phone LIKE ? OR username LIKE ? OR full_name LIKE ?
            ORDER BY joined_at DESC
            LIMIT 10
            """, (f"%{q}%", f"%{q}%", f"%{q}%"))
            rows = cur.fetchall()
            con.close()

            if not rows:
                await update.message.reply_text("نتیجه‌ای پیدا نشد.")
                return

            if len(rows) == 1:
                await update.message.reply_text(admin_user_text(rows[0]), reply_markup=admin_user_keyboard(rows[0][0]))
                return

            buttons = []
            for r in rows:
                buttons.append([
                    InlineKeyboardButton(
                        f"{r[2]} | {r[3] or 'بدون شماره'}",
                        callback_data=f"admin_user_{r[0]}"
                    )
                ])

            await update.message.reply_text(
                "چند نتیجه پیدا شد:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        if admin_mode == "send_voucher":
            order_id = context.user_data.get("order_id")
            code = text.strip()

            con = db()
            cur = con.cursor()
            cur.execute(
                "UPDATE orders SET voucher_code=?, status='delivered', updated_at=?, completed_at=? WHERE id=?",
                (code, now(), now(), order_id)
            )
            cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
            target = cur.fetchone()
            con.commit()
            con.close()

            context.user_data.clear()

            if target:
                await context.bot.send_message(
                    chat_id=target[0],
                    text=f"🎫 سفارش {ensure_order_identity(order_id, 'UV')[0]} تکمیل شد ✅\n\nکد Uvoucher:\n`{code}`",
                    parse_mode="Markdown"
                )

            await update.message.reply_text("ووچر ارسال شد ✅")
            return

        if admin_mode == "set_profit":
            try:
                profit = float(text.strip())
                set_setting("profit_percent", profit)
                context.user_data.clear()
                await update.message.reply_text(f"سود روی {profit}% تنظیم شد ✅")
            except Exception:
                await update.message.reply_text("عدد معتبر بفرست. مثال: 8")
            return

        if admin_mode == "set_card":
            set_setting("card_info", text.strip())
            context.user_data.clear()
            await update.message.reply_text("اطلاعات کارت ذخیره شد ✅")
            return

        if admin_mode == "set_fallback":
            try:
                rate = int(text.replace(",", "").strip())
                set_setting("fallback_rate", rate)
                context.user_data.clear()
                await update.message.reply_text(f"نرخ پشتیبان ذخیره شد: {rate:,} تومان ✅")
            except Exception:
                await update.message.reply_text("عدد معتبر بفرست.")
            return

        if admin_mode == "set_limit":
            limit_key = context.user_data.get("limit_key")
            try:
                amount = int(text.replace(",", "").strip())
                if amount < 0:
                    raise ValueError
            except Exception:
                await update.message.reply_text("عدد معتبر بفرست. برای نامحدود عدد 0 بفرست.")
                return

            set_setting(limit_key, amount)
            context.user_data.clear()
            await update.message.reply_text(f"سقف جدید ذخیره شد: {limit_text(amount)} ✅")
            return

    if mode == "bank_wait_card":
        card = text.replace(" ", "").replace("-", "").strip()
        if not card.isdigit() or len(card) != 16:
            await update.message.reply_text("شماره کارت نامعتبر است. لطفاً شماره کارت ۱۶ رقمی را ارسال کنید.")
            return

        context.user_data["bank_card"] = card
        context.user_data["mode"] = "bank_wait_sheba"
        await update.message.reply_text("حالا شماره شبا را ارسال کنید.\nمثال: IRxxxxxxxxxxxxxxxxxxxxxxxx")
        return

    if mode == "bank_wait_sheba":
        sheba = normalize_sheba(text)

        if not sheba.startswith("IR") or len(sheba) != 26:
            await update.message.reply_text("شماره شبا نامعتبر است. باید با IR شروع شود و ۲۶ کاراکتر باشد.")
            return

        card = context.user_data.get("bank_card")

        if not card:
            context.user_data.clear()
            await update.message.reply_text("اطلاعات کارت پیدا نشد. لطفاً دوباره حساب بانکی را ثبت کنید.", reply_markup=main_menu())
            return

        try:
            con = db()
            cur = con.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS bank_accounts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_number TEXT,
                sheba TEXT,
                bank_name TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            )
            """)

            cur.execute("""
            INSERT INTO bank_accounts(user_id, card_number, sheba, status, created_at, updated_at)
            VALUES(?,?,?,?,?,?)
            """, (user.id, card, sheba, "pending", now(), now()))

            bank_id = cur.lastrowid
            con.commit()
            con.close()

            context.user_data.clear()

            await update.message.reply_text(
                "✅ حساب بانکی شما ثبت شد و در انتظار بررسی ادمین قرار گرفت.",
                reply_markup=main_menu()
            )

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🏦 درخواست حساب بانکی جدید #{bank_id}\n\n"
                    f"کاربر: {user.full_name}\n"
                    f"آیدی: {user.id}\n"
                    f"یوزرنیم: @{user.username}\n"
                    f"کارت: {mask_card(card)}\n"
                    f"شبا: {sheba}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ بررسی حساب بانکی", callback_data=f"admin_bank_review_{bank_id}")]
                ])
            )
            return

        except Exception as e:
            print("BANK SHEBA ERROR:", repr(e))
            await update.message.reply_text("خطا در ثبت حساب بانکی. لطفاً دوباره تلاش کنید یا با پشتیبانی ارتباط بگیرید.")
            return

    if text == "🛒 خرید Uvoucher":
        context.user_data["mode"] = "buy_amount"
        await update.message.reply_text(
            "🛒 شما در مرحله وارد کردن مبلغ خرید هستید.\n\n"
            "لطفاً مبلغ دلاری موردنظر را وارد کرده یا از دکمه زیر استفاده کنید.\n\n"
            "مثال: 10",
            reply_markup=buy_start_keyboard()
        )
        return

    if mode == "buy_amount":
        try:
            amount = float(text.replace("$", "").strip())
            if amount <= 0:
                raise ValueError
        except Exception:
            await update.message.reply_text("فقط عدد معتبر وارد کن. مثال: 10")
            return

        rate = get_rate()
        price = int(amount * rate)

        row = get_user(user.id)
        daily_limit = get_daily_limit(row)
        today_total = get_today_total(user.id)

        if daily_limit != 0 and today_total + price > daily_limit:
            remaining = max(daily_limit - today_total, 0)
            await update.message.reply_text(
                f"❌ سقف خرید روزانه شما کافی نیست.\n\n"
                f"سقف روزانه: {daily_limit:,} تومان\n"
                f"خرید امروز: {today_total:,} تومان\n"
                f"باقیمانده: {remaining:,} تومان\n"
                f"مبلغ این سفارش: {price:,} تومان\n\n"
                "برای افزایش سقف، احراز هویت یا ارتقای سطح کاربری لازم است.",
                reply_markup=buy_start_keyboard()
            )
            return

        con = db()
        cur = con.cursor()
        cur.execute("""
        INSERT INTO orders(user_id, amount_usd, rate, price_toman, status, created_at, updated_at)
        VALUES(?,?,?,?,?,?,?)
        """, (user.id, amount, rate, price, "waiting_receipt", now(), now()))
        order_id = cur.lastrowid
        con.commit()
        con.close()

        try:
            identity = ensure_order_identity(order_id, "UV")
            order_number, tracking_code = identity if identity else (f"#{order_id}", "-")
        except Exception as e:
            logging.exception("order identity generation failed")
            order_number, tracking_code = f"#{order_id}", "-"

        context.user_data["mode"] = "receipt_choice"
        context.user_data["order_id"] = order_id

        await update.message.reply_text(
            f"✅ سفارش ثبت شد\n\n"
            f"شماره سفارش: {order_number}\n"
            f"کد رهگیری: {tracking_code}\n"
            f"مقدار: {amount}$\n"
            f"نرخ هر دلار: {rate:,} تومان\n"
            f"مبلغ پرداختی: {price:,} تومان\n\n"
            f"{get_setting('card_info', DEFAULT_CARD_INFO)}\n\n"
            "بعد از پرداخت، نوع ارسال اطلاعات واریز را انتخاب کن:",
            reply_markup=receipt_method_keyboard(order_id)
        )
        return

    if mode == "receipt_choice":
        order_id = context.user_data.get("order_id")
        await update.message.reply_text(
            "لطفاً نوع ارسال اطلاعات واریز را از دکمه‌های زیر انتخاب کن.",
            reply_markup=receipt_method_keyboard(order_id)
        )
        return

    if mode == "waiting_receipt_text":
        context.user_data["receipt_text"] = text.strip()
        context.user_data["mode"] = "waiting_tracking_code"
        await update.message.reply_text(
            "حالا شماره پیگیری / شماره ارجاع بانکی را ارسال کن.",
            reply_markup=flow_nav_keyboard("back_receipt_choice")
        )
        return

    if mode == "waiting_tracking_code":
        order_id = context.user_data.get("order_id")
        receipt_text = context.user_data.get("receipt_text", "")
        tracking_code = text.strip()
        final_receipt = f"رسید متنی:\n{receipt_text}\n\nشماره پیگیری / ارجاع:\n{tracking_code}"
        await save_receipt(update, context, order_id, final_receipt, False)
        return

    if mode == "waiting_receipt_photo":
        await update.message.reply_text(
            "لطفاً تصویر رسید تراکنش را ارسال کن.",
            reply_markup=flow_nav_keyboard("back_receipt_choice")
        )
        return

    if text == "👤 حساب کاربری":
        row = get_user(user.id)
        msg = (
            "👤 حساب کاربری شما\n\n"
            f"👤 نام: {row[2]}\n"
            f"🔗 یوزرنیم: @{row[1] if row[1] else 'ندارد'}\n"
            f"🆔 شناسه کاربری: {display_uid(row[0])}\n"
        f"تلگرام: {row[0]}\n"
            f"📱 شماره: {row[3]}\n"
            f"💰 کیف پول: {row[4]:,} تومان\n"
            f"🪪 احراز: {kyc_fa(row[5])}\n"
            f"⭐ سطح: {level_fa(row[6])}\n"
            f"📅 تاریخ عضویت: {row[8]}"
        )
        await update.message.reply_text("👤 حساب کاربری شما:", reply_markup=profile_keyboard(row))
        return

    if text == "🏦 حساب‌های بانکی":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM bank_accounts WHERE user_id=?", (user.id,))
        count = cur.fetchone()[0]
        con.close()

        if count > 0:
            await update.message.reply_text(
                "🏦 حساب‌های بانکی شما:",
                reply_markup=bank_accounts_keyboard(user.id)
            )
            return

        await update.message.reply_text(
            "🏦 حساب‌های بانکی\n\n"
            "برای واریز و برداشت، فقط حساب‌های بانکی تأییدشده قابل استفاده هستند.\n\n"
            "تنها حساب‌هایی که در تعهدنامه یا فرآیند احراز هویت ثبت شده‌اند، قابل تأیید خواهند بود.\n\n"
            "اگر حساب جدیدی دارید که در تعهدنامه ثبت نشده، ابتدا از طریق پشتیبانی درخواست ثبت آن را ارسال کنید.\n\n"
            "با انتخاب گزینه زیر، تأیید می‌کنید اطلاعات حساب متعلق به خودتان است.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ قوانین را می‌پذیرم", callback_data="bank_accept")],
                [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")]
            ])
        )
        return

    if text == "💰 کیف پول":
        row = get_user(user.id)
        await update.message.reply_text(
            f"💰 کیف پول شما\n\n"
            f"موجودی فعلی: {row[4]:,} تومان\n\n"
            "یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=wallet_keyboard()
        )
        return

    if text == "📦 سفارشات من":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user.id,))
        count = cur.fetchone()[0]
        con.close()

        if count == 0:
            await update.message.reply_text("هنوز سفارشی ثبت نکرده‌اید.")
            return

        await update.message.reply_text(
            "📦 سفارشات من\n\nبرای مشاهده جزئیات، روی سفارش موردنظر بزنید:",
            reply_markup=user_orders_inline_keyboard(user.id)
        )
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
            await update.message.reply_text("هنوز کدی تحویل نشده.")
            return

        msg = "🎫 کدهای خریداری شده:\n\n"
        for r in rows:
            msg += f"سفارش #{r[0]} | {r[1]}$\n`{r[2]}`\n{r[3]}\n\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text == "📞 پشتیبانی":
        context.user_data["mode"] = "support"
        await update.message.reply_text("پیام پشتیبانی رو بفرست.")
        return

    if mode == "support":
        context.user_data.clear()
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📞 پیام پشتیبانی\n\n"
                f"کاربر: {user.full_name}\n"
                f"آیدی: {user.id}\n"
                f"یوزرنیم: @{user.username}\n\n"
                f"{text}"
            )
        )
        await update.message.reply_text("پیامت ارسال شد ✅")
        return

    if text == "📖 راهنما":
        await update.message.reply_text(
            "📖 راهنما\n\n"
            "1. خرید Uvoucher رو بزن.\n"
            "2. مبلغ دلاری رو وارد کن.\n"
            "3. پرداخت کن و رسید بفرست.\n"
            "4. بعد از تأیید ادمین، کد ارسال میشه."
        )
        return

    await update.message.reply_text("از منوی پایین انتخاب کن.")


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    mode = context.user_data.get("mode")
    order_id = context.user_data.get("order_id")
    print("PHOTO HANDLER:", "user=", user.id, "mode=", mode, "order_id=", order_id)

    if not has_phone(user.id):
        await update.message.reply_text("اول شماره ثبت کن.", reply_markup=phone_menu())
        return

    if mode == "kyc_upload":
        photo = update.message.photo[-1].file_id

        con = db()
        cur = con.cursor()
        cur.execute(
            "UPDATE users SET kyc_status='pending' WHERE user_id=?",
            (user.id,)
        )
        cur.execute("""
        INSERT INTO kyc_requests(user_id, image_file_id, status, created_at, updated_at)
        VALUES(?,?,?,?,?)
        """, (user.id, photo, "pending", now(), now()))
        kyc_id = cur.lastrowid
        con.commit()
        con.close()

        context.user_data.clear()

        await update.message.reply_text(
            "✅ درخواست احراز شما ثبت شد.\n"
            "در انتظار بررسی ادمین باشید."
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید احراز", callback_data=f"kycapprove_{kyc_id}"),
                InlineKeyboardButton("❌ رد احراز", callback_data=f"kycreject_{kyc_id}")
            ]
        ])

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=(
                f"🪪 درخواست احراز جدید #{kyc_id}\n\n"
                f"کاربر: {user.full_name}\n"
                f"آیدی: {user.id}\n"
                f"یوزرنیم: @{user.username}\n"
            ),
            reply_markup=keyboard
        )
        return

    if mode == "waiting_receipt_photo":
        if not order_id:
            await update.message.reply_text("سفارش فعالی برای ثبت رسید پیدا نشد. لطفاً دوباره خرید را شروع کنید.")
            return

        photo = update.message.photo[-1].file_id
        await save_receipt(update, context, order_id, photo, True)
        return

    await update.message.reply_text(
        "عکس دریافت شد، اما الان در مرحله ارسال تصویر رسید نیستی.\n"
        "ابتدا دکمه «ارسال تصویر رسید تراکنش» را بزن."
    )
    return


async def send_admin_order_from_text(update, context, order_id, silent=False):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT id, user_id, amount_usd, rate, price_toman, status, voucher_code, created_at
    FROM orders
    WHERE id=?
    """, (order_id,))
    o = cur.fetchone()
    con.close()

    if not o:
        if not silent:
            await update.message.reply_text("سفارش پیدا نشد.")
        return False

    await update.message.reply_text(
        f"📦 سفارش {format_order_code(o[0], o[7])}\n\n"
        f"کاربر: {o[1]}\n"
        f"مقدار: {o[2]}$\n"
        f"نرخ: {o[3]:,} تومان\n"
        f"مبلغ: {o[4]:,} تومان\n"
        f"وضعیت: {order_status_fa(o[5])}\n"
        f"کد: {o[6] or 'ثبت نشده'}\n"
        f"تاریخ: {o[7]}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{o[0]}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_{o[0]}")
            ],
            [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{o[0]}")]
        ])
    )
    return True


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("دسترسی نداری.")
        return

    await update.message.reply_text("👨‍💼 پنل ادمین", reply_markup=admin_keyboard())


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "noop":
        await query.answer("این بخش فقط نمایشی است.")
        return

    if data == "noop":
        await query.answer("این بخش فقط نمایشی است.")
        return

    if data == "user_kyc":
        row = get_user(query.from_user.id)
        if row and row[5] == "verified":
            await query.message.reply_text("✅ احراز هویت شما قبلاً تأیید شده است.")
            return

        await query.message.reply_text(
            "🪪 احراز هویت MixVoucher\n\n"
            "برای ادامه یکی از گزینه‌های زیر را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ شروع احراز هویت", callback_data="kyc_start")],
                [InlineKeyboardButton("🖼 مشاهده تصویر نمونه", callback_data="kyc_sample")],
                [InlineKeyboardButton("🔙 حساب کاربری", callback_data="user_profile")]
            ])
        )
        return

    if data == "kyc_start":
        context.user_data.clear()
        context.user_data["mode"] = "kyc_upload"

        await query.message.reply_text(
            "🪪 احراز هویت MixVoucher\n\n"
            + get_setting("kyc_text", DEFAULT_KYC_TEXT)
            + "\n\n✅ بعد از آماده کردن برگه، فقط یک عکس واضح از همان برگه ارسال کن."
        )
        return

    if data == "kyc_sample":
        try:
            with open(KYC_SAMPLE_IMAGE_PATH, "rb") as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption="🖼 نمونه صحیح برگه احراز هویت MixVoucher"
                )
        except FileNotFoundError:
            await query.message.reply_text(
                "تصویر نمونه هنوز روی سرور قرار نگرفته است.\n"
                "فایل را با نام kyc_sample.png داخل پوشه assets بگذار."
            )
        return

    if data == "user_profile":
        row = get_user(query.from_user.id)
        msg = (
            "👤 حساب کاربری شما\n\n"
            f"👤 نام: {row[2]}\n"
            f"🔗 یوزرنیم: @{row[1] if row[1] else 'ندارد'}\n"
            f"🆔 شناسه کاربری: {display_uid(row[0])}\n"
        f"تلگرام: {row[0]}\n"
            f"📱 شماره: {row[3]}\n"
            f"💰 کیف پول: {row[4]:,} تومان\n"
            f"🪪 احراز: {kyc_fa(row[5])}\n"
            f"⭐ سطح: {level_fa(row[6])}\n"
            f"📅 تاریخ عضویت: {row[8]}"
        )
        await query.edit_message_text("👤 حساب کاربری شما:", reply_markup=profile_keyboard(row))
        return

    if data == "user_orders":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (query.from_user.id,))
        count = cur.fetchone()[0]
        con.close()

        if count == 0:
            await query.edit_message_text(
                "هنوز سفارشی نداری.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 حساب کاربری", callback_data="user_profile")]
                ])
            )
            return

        await query.edit_message_text(
            "📦 سفارشات شما:",
            reply_markup=user_orders_keyboard(query.from_user.id)
        )
        return

    if (
        data.startswith("user_order_")
        and not data.startswith("user_order_view_")
        and not data.startswith("user_order_receipt_")
    ):
        order_id = int(data.split("_")[2])
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, amount_usd, rate, price_toman, status, voucher_code, created_at
        FROM orders
        WHERE id=? AND user_id=?
        """, (order_id, query.from_user.id))
        o = cur.fetchone()
        con.close()

        if not o:
            await query.edit_message_text("سفارش پیدا نشد.")
            return

        await query.edit_message_text(
            f"📦 جزئیات سفارش #{o[0]}\\n\\n"
            f"مقدار: {o[2]}$\\n"
            f"نرخ: {o[3]:,} تومان\\n"
            f"مبلغ: {o[4]:,} تومان\\n"
            f"وضعیت: {order_status_fa(o[5])}\\n"
            f"کد: {o[6] or 'تحویل نشده'}\\n"
            f"تاریخ: {o[7]}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 سفارشات من", callback_data="user_orders")]
            ])
        )
        return

    # Public navigation callbacks - must run before admin access check
    if data == "back_main":
        context.user_data.clear()
        await query.message.reply_text("به منوی اصلی برگشتی ✅", reply_markup=main_menu())
        return

    if data == "back_buy_amount":
        context.user_data["mode"] = "buy_amount"
        context.user_data.pop("receipt_text", None)
        await query.message.reply_text(
            "🛒 شما در مرحله وارد کردن مبلغ خرید هستید.\n\n"
            "لطفاً مبلغ دلاری موردنظر را وارد کرده یا از دکمه زیر استفاده کنید.\n\n"
            "مثال: 10",
            reply_markup=buy_start_keyboard()
        )
        return

    if data == "back_receipt_choice":
        order_id = context.user_data.get("order_id")
        context.user_data["mode"] = "receipt_choice"
        context.user_data.pop("receipt_text", None)
        await query.message.reply_text(
            "نوع ارسال اطلاعات واریز را انتخاب کنید:",
            reply_markup=receipt_method_keyboard(order_id)
        )
        return

    if data.startswith("receipt_photo_"):
        order_id = int(data.split("_")[2])
        context.user_data["mode"] = "waiting_receipt_photo"
        context.user_data["order_id"] = order_id
        await query.message.reply_text(
            "📷 لطفاً تصویر رسید تراکنش را ارسال کنید.",
            reply_markup=flow_nav_keyboard("back_receipt_choice")
        )
        return

    if data.startswith("receipt_text_"):
        order_id = int(data.split("_")[2])
        context.user_data["mode"] = "waiting_receipt_text"
        context.user_data["order_id"] = order_id
        await query.message.reply_text(
            "📝 متن رسید تراکنش را ارسال کنید.\nبعد از آن، شماره پیگیری بانکی از شما دریافت می‌شود.",
            reply_markup=flow_nav_keyboard("back_receipt_choice")
        )
        return

    if data == "bank_accept":
        await query.message.reply_text(
            "شماره کارت ۱۶ رقمی خود را ارسال کنید:",
            reply_markup=back_to_main_keyboard()
        )
        context.user_data["mode"] = "bank_wait_card"
        return

    if data == "bank_add":
        await query.message.reply_text(
            "شماره کارت ۱۶ رقمی حساب جدید را ارسال کنید:",
            reply_markup=back_to_main_keyboard()
        )
        context.user_data["mode"] = "bank_wait_card"
        return

    if data == "user_orders":
        await query.message.reply_text(
            "📦 سفارشات من\n\nبرای مشاهده جزئیات، روی سفارش موردنظر بزنید:",
            reply_markup=user_orders_inline_keyboard(query.from_user.id)
        )
        return

    if data.startswith("user_order_view_"):
        order_id = int(data.split("_")[3])
        await query.message.reply_text(
            order_detail_text(order_id, query.from_user.id),
            reply_markup=user_order_detail_keyboard(order_id)
        )
        return

    if data == "user_support":
        context.user_data["mode"] = "support"
        await query.message.reply_text("پیام خود را برای پشتیبانی ارسال کنید.")
        return

    if data.startswith("user_order_receipt_"):
        order_id = int(data.split("_")[3])

        con = db()
        cur = con.cursor()
        cur.execute("SELECT receipt FROM orders WHERE id=? AND user_id=?", (order_id, query.from_user.id))
        row = cur.fetchone()
        con.close()

        if not row or not row[0]:
            await query.message.reply_text("برای این سفارش هنوز رسیدی ثبت نشده است.")
            return

        receipt = row[0]

        if str(receipt).startswith("Ag") or str(receipt).startswith("BQ"):
            await query.message.reply_photo(photo=receipt, caption="🧾 رسید پرداخت سفارش")
        else:
            await query.message.reply_text(f"🧾 رسید پرداخت سفارش:\n\n{receipt}")

        return

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("دسترسی نداری.")
        return

    if data.startswith("admin_bank_approve_"):
        bank_id = int(data.split("_")[3])
        context.user_data["admin_mode"] = "bank_set_name"
        context.user_data["bank_id"] = bank_id
        await query.message.reply_text("نام بانک را وارد کنید. مثال: صادرات")
        return

    if data.startswith("admin_bank_reject_"):
        bank_id = int(data.split("_")[3])
        context.user_data["admin_mode"] = "bank_reject_reason"
        context.user_data["bank_id"] = bank_id
        await query.message.reply_text("دلیل رد حساب بانکی را وارد کنید.")
        return

    if data == "admin_banks":
        await query.edit_message_text(
            "🏦 مدیریت حساب‌های بانکی",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏳ در انتظار بررسی", callback_data="admin_banks_pending")],
                [InlineKeyboardButton("✅ تأیید شده", callback_data="admin_banks_approved")],
                [InlineKeyboardButton("❌ رد شده", callback_data="admin_banks_rejected")],
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
            ])
        )
        return

    if data.startswith("admin_banks_"):
        status = data.replace("admin_banks_", "")

        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, card_number, sheba, bank_name, status
        FROM bank_accounts
        WHERE status=?
        ORDER BY id DESC
        LIMIT 20
        """, (status,))
        rows = cur.fetchall()
        con.close()

        title_map = {
            "pending": "⏳ حساب‌های در انتظار بررسی",
            "approved": "✅ حساب‌های تأیید شده",
            "rejected": "❌ حساب‌های رد شده",
        }

        if not rows:
            await query.edit_message_text(
                f"{title_map.get(status, 'حساب‌های بانکی')}\n\nموردی وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 مدیریت حساب‌های بانکی", callback_data="admin_banks")]
                ])
            )
            return

        buttons = []
        for r in rows:
            bank_id, user_id, card, sheba, bank_name, st = r
            buttons.append([
                InlineKeyboardButton(
                    f"#{bank_id} | {bank_display_name(bank_name, card)} | {user_id}",
                    callback_data=f"admin_bank_view_{bank_id}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 مدیریت حساب‌های بانکی", callback_data="admin_banks")])

        await query.edit_message_text(
            title_map.get(status, "حساب‌های بانکی"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("admin_bank_view_"):
        bank_id = int(data.split("_")[3])

        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, card_number, sheba, bank_name, status, created_at
        FROM bank_accounts
        WHERE id=?
        """, (bank_id,))
        r = cur.fetchone()
        con.close()

        if not r:
            await query.edit_message_text("حساب بانکی پیدا نشد.")
            return

        bank_id, user_id, card, sheba, bank_name, status, created_at = r
        status_fa = {
            "pending": "در انتظار بررسی",
            "approved": "تأیید شده",
            "rejected": "رد شده",
        }.get(status, status)

        await query.edit_message_text(
            f"🏦 جزئیات حساب بانکی #{bank_id}\n\n"
            f"کاربر: {user_id}\n"
            f"بانک: {bank_name or 'ثبت نشده'}\n"
            f"کارت: {card}\n"
            f"شبا: {sheba}\n"
            f"وضعیت: {status_fa}\n"
            f"تاریخ ثبت: {created_at}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأیید", callback_data=f"admin_bank_approve_{bank_id}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"admin_bank_reject_{bank_id}")
                ],
                [InlineKeyboardButton("🔙 مدیریت حساب‌ها", callback_data="admin_banks")]
            ])
        )
        return

    if data == "admin_home":
        await query.edit_message_text("👨‍💼 پنل ادمین", reply_markup=admin_keyboard())
        return

    if data == "admin_pending":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, amount_usd, price_toman, status
        FROM orders
        WHERE status IN ('waiting_admin', 'approved')
        ORDER BY id DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text("سفارشی در انتظار نیست.", reply_markup=admin_keyboard())
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"#{r[0]} | {r[1]}$ | {order_status_fa(r[3])}",
                    callback_data=f"order_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "📥 سفارش‌های در انتظار:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data == "admin_orders":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, amount_usd, price_toman, status
        FROM orders
        ORDER BY id DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text("هنوز سفارشی ثبت نشده.", reply_markup=admin_keyboard())
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"#{r[0]} | {r[1]}$ | {order_status_fa(r[3])}",
                    callback_data=f"order_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "📦 آخرین سفارش‌ها:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data == "admin_users":
        await query.edit_message_text(
            "👥 مدیریت کاربران\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 جستجوی کاربر یا سفارش", callback_data="admin_search")],
                [InlineKeyboardButton("🆕 آخرین کاربران", callback_data="admin_latest_users")],
                [InlineKeyboardButton("🪪 احرازهای در انتظار", callback_data="admin_kyc")],
                [InlineKeyboardButton("🚫 کاربران مسدود", callback_data="admin_blocked_users")],
                [InlineKeyboardButton("⭐ کاربران حرفه‌ای", callback_data="admin_pro_users")],
                [InlineKeyboardButton("🔙 پنل ادمین", callback_data="admin_home")]
            ])
        )
        return

    if data == "admin_search":
        context.user_data["admin_mode"] = "admin_search"
        await query.message.reply_text(
            "🔍 شناسه موردنظر را ارسال کن.\n\n"
            "موارد قابل جستجو:\n"
            "• شماره سفارش مثل MV-20260626-000001 یا 1\n"
            "• آیدی عددی کاربر\n"
            "• شماره موبایل\n"
            "• یوزرنیم\n"
            "• نام کاربر"
        )
        return

    if data == "admin_latest_users":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT 10")
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text("کاربری ثبت نشده.", reply_markup=admin_keyboard())
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"{r[2]} | {r[3] or 'بدون شماره'}",
                    callback_data=f"admin_user_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")])
        await query.edit_message_text("🆕 آخرین کاربران:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "admin_blocked_users":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE is_blocked=1 ORDER BY joined_at DESC LIMIT 10")
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "کاربر مسدودی وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")]])
            )
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"{r[2]} | {r[3] or 'بدون شماره'}",
                    callback_data=f"admin_user_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")])
        await query.edit_message_text("🚫 کاربران مسدود:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("admin_user_level_"):
        user_id = int(data.split("_")[3])
        await query.edit_message_text(
            "⭐ سطح جدید کاربر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ معمولی", callback_data=f"admin_set_level_{user_id}_normal")],
                [InlineKeyboardButton("⭐⭐ پیشرفته", callback_data=f"admin_set_level_{user_id}_advanced")],
                [InlineKeyboardButton("⭐⭐⭐ حرفه‌ای", callback_data=f"admin_set_level_{user_id}_pro")],
                [InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"admin_user_{user_id}")]
            ])
        )
        return

    if data.startswith("admin_set_level_"):
        parts = data.split("_")
        user_id = int(parts[3])
        level = parts[4]

        con = db()
        cur = con.cursor()
        cur.execute("UPDATE users SET user_level=? WHERE user_id=?", (level, user_id))
        con.commit()
        con.close()

        row = get_user(user_id)
        await query.edit_message_text(
            f"سطح کاربر با موفقیت به {level_fa(level)} تغییر کرد ✅\n\n" + admin_user_text(row),
            reply_markup=admin_user_keyboard(user_id)
        )
        return

    if data.startswith("admin_user_kyc_"):
        user_id = int(data.split("_")[3])
        await query.edit_message_text(
            "🪪 وضعیت احراز جدید را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تأیید شده", callback_data=f"admin_set_kyc_{user_id}_verified")],
                [InlineKeyboardButton("⏳ در انتظار بررسی", callback_data=f"admin_set_kyc_{user_id}_pending")],
                [InlineKeyboardButton("❌ رد شده", callback_data=f"admin_set_kyc_{user_id}_rejected")],
                [InlineKeyboardButton("⭕ احراز نشده", callback_data=f"admin_set_kyc_{user_id}_not_started")],
                [InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"admin_user_{user_id}")]
            ])
        )
        return

    if data.startswith("admin_set_kyc_"):
        parts = data.split("_")
        user_id = int(parts[3])
        status = "_".join(parts[4:])

        con = db()
        cur = con.cursor()
        cur.execute("UPDATE users SET kyc_status=? WHERE user_id=?", (status, user_id))
        con.commit()
        con.close()

        row = get_user(user_id)
        await query.edit_message_text(
            f"وضعیت احراز کاربر به {kyc_fa(status)} تغییر کرد ✅\n\n" + admin_user_text(row),
            reply_markup=admin_user_keyboard(user_id)
        )
        return

    if data.startswith("admin_user_block_"):
        user_id = int(data.split("_")[3])

        con = db()
        cur = con.cursor()
        cur.execute("SELECT is_blocked FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()

        if not row:
            con.close()
            await query.edit_message_text("کاربر پیدا نشد.")
            return

        new_status = 0 if int(row[0]) == 1 else 1
        cur.execute("UPDATE users SET is_blocked=? WHERE user_id=?", (new_status, user_id))
        con.commit()
        con.close()

        row = get_user(user_id)
        msg = "کاربر آزاد شد ✅" if new_status == 0 else "کاربر مسدود شد 🚫"

        await query.edit_message_text(
            msg + "\n\n" + admin_user_text(row),
            reply_markup=admin_user_keyboard(user_id)
        )
        return

    if (
        data.startswith("admin_user_")
        and not data.startswith("admin_user_orders_")
        and not data.startswith("admin_user_level_")
        and not data.startswith("admin_user_kyc_")
        and not data.startswith("admin_user_block_")
    ):
        user_id = int(data.split("_")[2])
        row = get_user(user_id)

        if not row:
            await query.edit_message_text("کاربر پیدا نشد.")
            return

        await query.edit_message_text(admin_user_text(row), reply_markup=admin_user_keyboard(user_id))
        return

    if data.startswith("admin_user_orders_"):
        user_id = int(data.split("_")[3])
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, amount_usd, price_toman, status, created_at
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
        """, (user_id,))
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "این کاربر سفارشی ندارد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"admin_user_{user_id}")]])
            )
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"{format_order_code(r[0], r[4])} | {r[1]}$ | {order_status_fa(r[3])}",
                    callback_data=f"order_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 پروفایل کاربر", callback_data=f"admin_user_{user_id}")])
        await query.edit_message_text("📦 سفارشات کاربر:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "admin_pro_users":
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE user_level='pro' ORDER BY joined_at DESC LIMIT 10")
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text(
                "فعلاً کاربر حرفه‌ای وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")]
                ])
            )
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"{r[2]} | {r[3] or 'بدون شماره'}",
                    callback_data=f"admin_user_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 مدیریت کاربران", callback_data="admin_users")])
        await query.edit_message_text("⭐ کاربران حرفه‌ای:", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data == "admin_kyc":
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, status, created_at
        FROM kyc_requests
        WHERE status='pending'
        ORDER BY id DESC
        LIMIT 10
        """)
        rows = cur.fetchall()
        con.close()

        if not rows:
            await query.edit_message_text("درخواست احراز در انتظاری وجود ندارد.", reply_markup=admin_keyboard())
            return

        buttons = []
        for r in rows:
            buttons.append([
                InlineKeyboardButton(
                    f"#{r[0]} | کاربر {r[1]} | {r[3]}",
                    callback_data=f"kycview_{r[0]}"
                )
            ])

        buttons.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_home")])

        await query.edit_message_text(
            "🪪 احرازهای در انتظار:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("kycview_"):
        kyc_id = int(data.split("_")[1])
        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, image_file_id, status, created_at
        FROM kyc_requests
        WHERE id=?
        """, (kyc_id,))
        k = cur.fetchone()
        con.close()

        if not k:
            await query.edit_message_text("درخواست احراز پیدا نشد.")
            return

        await query.message.reply_photo(
            photo=k[2],
            caption=(
                f"🪪 جزئیات احراز #{k[0]}\n\n"
                f"کاربر: {k[1]}\n"
                f"وضعیت: {k[3]}\n"
                f"تاریخ: {k[4]}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأیید", callback_data=f"kycapprove_{k[0]}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"kycreject_{k[0]}")
                ],
                [InlineKeyboardButton("🔙 احرازها", callback_data="admin_kyc")]
            ])
        )
        return

    if data == "admin_settings":
        await query.edit_message_text(
            f"⚙️ تنظیمات ربات\n\n"
            f"درصد سود: {get_setting('profit_percent', DEFAULT_PROFIT_PERCENT)}%\n"
            f"نرخ پشتیبان: {int(get_setting('fallback_rate', DEFAULT_FALLBACK_RATE)):,} تومان\n\n"
            f"اطلاعات کارت:\n{get_setting('card_info', DEFAULT_CARD_INFO)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ تغییر سود", callback_data="set_profit")],
                [InlineKeyboardButton("💳 تغییر کارت", callback_data="set_card")],
                [InlineKeyboardButton("💵 تغییر نرخ پشتیبان", callback_data="set_fallback")],
                [InlineKeyboardButton("🚧 سقف خرید روزانه", callback_data="admin_limits")],
                [InlineKeyboardButton("🔙 برگشت", callback_data="admin_home")]
            ])
        )
        return

    if data == "set_profit":
        context.user_data["admin_mode"] = "set_profit"
        await query.message.reply_text("درصد سود جدید رو بفرست. مثال: 8")
        return

    if data == "set_card":
        context.user_data["admin_mode"] = "set_card"
        await query.message.reply_text("اطلاعات کارت جدید رو کامل بفرست.")
        return

    if data == "set_fallback":
        context.user_data["admin_mode"] = "set_fallback"
        await query.message.reply_text("نرخ پشتیبان هر دلار رو به تومان بفرست.")
        return

    if data == "admin_limits":
        await query.edit_message_text(
            "🚧 سقف خرید روزانه\n\n"
            f"❌ احراز نشده: {limit_text(get_setting('limit_unverified', '500000'))}\n"
            f"⭐ معمولی: {limit_text(get_setting('limit_normal', '3000000'))}\n"
            f"⭐⭐ پیشرفته: {limit_text(get_setting('limit_advanced', '20000000'))}\n"
            f"⭐⭐⭐ حرفه‌ای: {limit_text(get_setting('limit_pro', '0'))}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ تغییر سقف احراز نشده", callback_data="setlimit_limit_unverified")],
                [InlineKeyboardButton("⭐ تغییر سقف معمولی", callback_data="setlimit_limit_normal")],
                [InlineKeyboardButton("⭐⭐ تغییر سقف پیشرفته", callback_data="setlimit_limit_advanced")],
                [InlineKeyboardButton("⭐⭐⭐ تغییر سقف حرفه‌ای", callback_data="setlimit_limit_pro")],
                [InlineKeyboardButton("🔙 تنظیمات", callback_data="admin_settings")]
            ])
        )
        return

    if data.startswith("setlimit_"):
        key = data.replace("setlimit_", "")
        context.user_data["admin_mode"] = "set_limit"
        context.user_data["limit_key"] = key
        await query.message.reply_text(
            "سقف جدید را به تومان ارسال کن.\n\n"
            "مثال:\n3000000\n\n"
            "برای نامحدود عدد 0 را بفرست."
        )
        return

    if data.startswith("order_"):
        order_id = int(data.split("_")[1])

        con = db()
        cur = con.cursor()
        cur.execute("""
        SELECT id, user_id, amount_usd, rate, price_toman, status, voucher_code, created_at
        FROM orders
        WHERE id=?
        """, (order_id,))
        o = cur.fetchone()
        con.close()

        if not o:
            await query.edit_message_text("سفارش پیدا نشد.")
            return

        await query.edit_message_text(
            f"📦 سفارش #{o[0]}\n\n"
            f"کاربر: {o[1]}\n"
            f"مقدار: {o[2]}$\n"
            f"نرخ: {o[3]:,} تومان\n"
            f"مبلغ: {o[4]:,} تومان\n"
            f"وضعیت: {order_status_fa(o[5])}\n"
            f"کد: {o[6] or 'ثبت نشده'}\n"
            f"تاریخ: {o[7]}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{order_id}"),
                    InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}")
                ],
                [InlineKeyboardButton("🎫 ارسال ووچر", callback_data=f"deliver_{order_id}")],
                [InlineKeyboardButton("🔙 برگشت", callback_data="admin_pending")]
            ])
        )
        return

    if data.startswith("kycapprove_") or data.startswith("kycreject_"):
        action, kyc_id_text = data.split("_")
        kyc_id = int(kyc_id_text)

        con = db()
        cur = con.cursor()
        cur.execute("SELECT user_id FROM kyc_requests WHERE id=?", (kyc_id,))
        row = cur.fetchone()

        if not row:
            con.close()
            await query.edit_message_text("درخواست احراز پیدا نشد.")
            return

        target_user = row[0]

        if action == "kycapprove":
            cur.execute(
                "UPDATE kyc_requests SET status='approved', updated_at=? WHERE id=?",
                (now(), kyc_id)
            )
            cur.execute(
                "UPDATE users SET kyc_status='verified' WHERE user_id=?",
                (target_user,)
            )
            con.commit()
            con.close()

            await context.bot.send_message(
                chat_id=target_user,
                text="✅ احراز هویت شما با موفقیت تأیید شد."
            )
            await query.edit_message_caption("✅ احراز هویت تأیید شد.")
            return

        if action == "kycreject":
            con.close()
            context.user_data["admin_mode"] = "kyc_reject_reason"
            context.user_data["kyc_id"] = kyc_id
            context.user_data["target_user"] = target_user
            await query.message.reply_text("دلیل رد احراز هویت را ارسال کن.")
            return

    if data.startswith("approve_") or data.startswith("reject_") or data.startswith("deliver_"):
        action, order_id_text = data.split("_")
        order_id = int(order_id_text)

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
                text=f"✅ سفارش {ensure_order_identity(order_id, 'UV')[0]} تأیید شد.\nدر انتظار ارسال کد باشید."
            )
            await query.edit_message_text("سفارش تأیید شد ✅")
            return

        if action == "reject":
            con.close()
            context.user_data["admin_mode"] = "order_reject_reason"
            context.user_data["order_id"] = order_id

            await query.message.reply_text(
                f"❌ لطفاً دلیل رد سفارش {ensure_order_identity(order_id, 'UV')[0]} را ارسال کن:"
            )
            await query.edit_message_text("در انتظار دریافت دلیل رد سفارش...")
            return

        if action == "deliver":
            con.close()
            context.user_data["admin_mode"] = "send_voucher"
            context.user_data["order_id"] = order_id
            await query.message.reply_text(f"کد Uvoucher سفارش #{order_id} رو بفرست.")
            return


def main():
    print("RUNNING FILE:", __file__)

    init_db()

    app = Application.builder().token(BOT_TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("MixVoucher MVP is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
