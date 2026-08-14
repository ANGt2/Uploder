import sqlite3
from config import DB_NAME, DEFAULT_CARD_INFO, DEFAULT_FALLBACK_RATE, DEFAULT_KYC_TEXT, DEFAULT_PROFIT_PERCENT
from utils import today


def db():
    return sqlite3.connect(DB_NAME)


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
    }

    for key, value in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

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
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
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


def user_has_phone(user_id):
    row = get_user(user_id)
    return bool(row and row[3])


def get_today_total(user_id):
    con = db()
    cur = con.cursor()
    cur.execute("""
    SELECT COALESCE(SUM(price_toman), 0)
    FROM orders
    WHERE user_id=? AND status != 'rejected' AND substr(created_at, 1, 10)=?
    """, (user_id, today()))
    total = cur.fetchone()[0]
    con.close()
    return int(total or 0)
