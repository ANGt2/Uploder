import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import datetime

TOKEN = '8470592467:AAHiR-7sfNAopvNdnd5iHVHI1bRfJ3zQvI8'
ADMIN_ID = 5927935256
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

class DatabaseManager:
    def __init__(self, db_name="pishgam_ai.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            join_date TEXT,
            balance INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price INTEGER,
            stock INTEGER
        )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            status TEXT,
            message TEXT
        )''')
        self.conn.commit()

    def add_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        if not self.cursor.fetchone():
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO users (user_id, join_date) VALUES (?, ?)", (user_id, date))
            self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return self.cursor.fetchone()

    def get_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

db = DatabaseManager()

def main_menu_keyboard(is_admin=False):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🛒 فروشگاه محصولات"),
        KeyboardButton("💳 کیف پول")
    )
    markup.add(
        KeyboardButton("👤 حساب کاربری من"),
        KeyboardButton("📞 پشتیبانی")
    )
    markup.add(KeyboardButton("ℹ️ درباره Pishgam AI"))
    if is_admin:
        markup.add(KeyboardButton("🔐 پنل مدیریت"))
    return markup

def admin_panel_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 داشبورد آمار", callback_data="admin_stats"),
        InlineKeyboardButton("➕ مدیریت محصولات", callback_data="admin_products")
    )
    markup.add(
        InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
        InlineKeyboardButton("💰 امور مالی", callback_data="admin_finance")
    )
    markup.add(InlineKeyboardButton("📢 پیام همگانی (Broadcast)", callback_data="admin_broadcast"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    db.add_user(message.from_user.id)
    is_admin = (message.from_user.id == ADMIN_ID)
    text = (
        "<b>با سلام و احترام.</b>\n"
        "به ربات رسمی فروشگاه <b>Pishgam AI</b> خوش آمدید.\n\n"
        "🔹 مرجع تخصصی خدمات و محصولات هوش مصنوعی.\n"
        "جهت استفاده از خدمات، لطفاً از منوی زیر استفاده نمایید."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard(is_admin))

@bot.message_handler(func=lambda message: message.text == "👤 حساب کاربری من")
def my_account(message):
    user_data = db.get_user(message.from_user.id)
    if user_data:
        status = "مسدود" if user_data[3] else "فعال"
        text = (
            "<b>👤 اطلاعات حساب کاربری شما:</b>\n\n"
            f"▫️ <b>شناسه کاربری:</b> <code>{user_data[0]}</code>\n"
            f"▫️ <b>موجودی:</b> {user_data[2]:,} تومان\n"
            f"▫️ <b>وضعیت حساب:</b> {status}\n"
            f"▫️ <b>تاریخ عضویت:</b> {user_data[1]}\n"
        )
        bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "💳 کیف پول")
def wallet(message):
    user_data = db.get_user(message.from_user.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ افزایش موجودی", callback_data="add_balance"))
    text = (
        "<b>💳 کیف پول اختصاصی</b>\n\n"
        f"موجودی فعلی شما: <b>{user_data[2]:,} تومان</b>\n\n"
        "جهت افزایش موجودی، بر روی دکمه زیر کلیک نمایید."
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "ℹ️ درباره Pishgam AI")
def about_us(message):
    text = (
        "<b>شرکت Pishgam AI</b>\n\n"
        "ارائه‌دهنده رسمی خدمات هوش مصنوعی اعم از API، اکانت‌های پریمیوم و پرامپت‌های تخصصی.\n\n"
        "<b>قوانین استفاده:</b>\n"
        "۱. تمامی تراکنش‌ها تابع قوانین تجارت الکترونیک می‌باشد.\n"
        "۲. پشتیبانی در ساعات اداری پاسخگوی سوالات شما خواهد بود."
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "🔐 پنل مدیریت" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    text = "<b>🔐 به پنل مدیریت Pishgam AI خوش آمدید.</b>\n\nلطفاً بخش مورد نظر را انتخاب نمایید:"
    bot.send_message(message.chat.id, text, reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data == "admin_stats":
        total_users = db.get_stats()
        text = (
            "<b>📊 داشبورد آمار Pishgam AI</b>\n\n"
            f"👥 <b>تعداد کل کاربران:</b> {total_users}\n"
            "وضعیت سیستم: پایدار 🟢"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text)
    elif call.data == "admin_broadcast":
        bot.send_message(call.message.chat.id, "جهت ارسال پیام همگانی، پیام خود را با دستور /broadcast ارسال کنید.")
        bot.answer_callback_query(call.id)

if __name__ == '__main__':
    print("Pishgam AI Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
