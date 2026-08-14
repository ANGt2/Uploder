git remote -v
..
cd ~/mvlite_bot
git remote remove origin 2>/dev/null
git remote add origin https://github.com/ANGt2/Malcolmo.git
git remote -v
git push -u origin main
cd ~/mvlite_bot
git remote -v
git push -u origin main
pkill -f "python app.py" 2>/dev/null || true
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "app.py" 2>/dev/null || true
ps -A | grep -E "python|app.py"
pkill -f "app.py" 2>/dev/null || true
pkill -f "python" 2>/dev/null || true
ps -A | grep -E "python|app.py"
pkill -f "app.py" 2>/dev/null || true
pkill -f "python" 2>/dev/null || true
ps -A | grep -E "python|app.py"
t
cd ~/mvlite_bot
git add .
git commit -m "Update"
git push
cd ~/mvlite_bot
grep "MVLite" app.py
cd ~/mvlite_bot || exit 1
sed -i 's/print("MVLite Part 03 is running...")/print(f"{APP_NAME} {APP_VERSION} is running...")/' app.py
python -m py_compile app.py
git add app.py
git commit -m "Fix release startup log"
git push
sed -i 's/MVLite - Part 03 Wallet \/ Payments \/ Receipts/MVLite Release 1.0/' app.py
git add app.py
git commit -m "Update release title"
git push
cd ~/mvlite_bot || exit 1
sed -i 's/MVLite - Part 03 Wallet \/ Payments \/ Receipts/MVLite Release 1.0/' app.py
sed -i 's/print("MVLite Part 03 is running...")/print(f"{APP_NAME} {APP_VERSION} is running...")/' app.py
python -m py_compile app.py
git add app.py
git commit -m "Fix release title and startup log"
git push
cd ~/mvlite_bot || exit 1
sed -i 's/MVLite - Part 03 Wallet \/ Payments \/ Receipts/MVLite Release 1.0/' app.py
sed -i 's/print("MVLite Part 03 is running...")/print(f"{APP_NAME} {APP_VERSION} is running...")/' app.py
echo "===== بررسی تغییرات ====="
grep -nE 'MVLite Release|is running' app.py
python -m py_compile app.py && git add app.py && git commit -m "Fix release title and startup log" && git push
cd ~/mvlite_bot
git show origin/main:app.py | grep -nE 'MVLite Release|is running'
cd ~/mvlite_bot
git commit --allow-empty -m "Trigger Railway redeploy"
git push
cd ~/mvlite_bot
git commit --allow-empty -m "Trigger Railway redeploy"
git push
cd ~/mvlite_bot
git add .
git commit -m "Update bot"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_PART_11_API_MANAGER_PHASE1.txt ~/
cd ~
bash MVLITE_PART_11_API_MANAGER_PHASE1.txt
cd ~/mvlite_bot
tar -czf /sdcard/Download/AAA_MVLITE_API_PHASE1_$(date +%Y%m%d_%H%M).tar.gz .
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_PART_11_API_MANAGER_PHASE1_FIXED.txt ~/
cd ~
bash MVLITE_PART_11_API_MANAGER_PHASE1_FIXED.txt
cd ~/mvlite_bot
git add .
git commit -m "Add API manager phase 1"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_02_SYMBOLS_GENERIC_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_02_SYMBOLS_GENERIC_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add generic API symbols phase 2"
git push
/admin
cd ~/mvlite_bot
tar -czf /sdcard/Download/AAA_MVLITE_API_PHASE02_$(date +%Y%m%d_%H%M).tar.gz .
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_03_PRODUCT_BINDING_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_03_PRODUCT_BINDING_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add API product binding phase 3"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_04_PRICE_ENGINE_AUTO_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_04_PRICE_ENGINE_AUTO_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add automatic price engine phase 4"
git push
cd ~/mvlite_bot
grep -n "موتور قیمت خودکار" app.py
grep -n 'admin:price_engine' app.py
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_05_IRAN_PROFILES_FIXED_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_05_IRAN_PROFILES_FIXED_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add Iranian API profiles phase 5"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_06_MULTI_PROVIDER_FAILOVER_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_06_MULTI_PROVIDER_FAILOVER_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add multi provider failover phase 6"
git push
cd ~/mvlite_bot
git add .
git commit -m "Add multi provider failover phase 6"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_API_PHASE_07_PROVIDER_BACKUP_HEALTH_20260710.txt ~/
cd ~
bash MVLITE_API_PHASE_07_PROVIDER_BACKUP_HEALTH_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add provider backup and health phase 7"
git push
cd ~/mvlite_bot && FILE="AAA_MVLITE_VOUCHER_ORDERS_PHASE08_$(date +%Y%m%d_%H%M%S).tar.gz" && tar -czf "/storage/emulated/0/Download/$FILE" . && echo "✅ /storage/emulated/0/Download/$FILE"
cd ~/mvlite_bot && BACKUP="AAA_MVLITE_BEFORE_PHASE08_PART01_$(date +%Y%m%d_%H%M%S).tar.gz" && tar -czf "/storage/emulated/0/Download/$BACKUP" . && cp /storage/emulated/0/Download/MVLITE_PHASE08_PART01.patch . && patch --dry-run -p0 < MVLITE_PHASE08_PART01.patch && patch -p0 < MVLITE_PHASE08_PART01.patch && python -m py_compile app.py && echo "✅ Part 8.1 نصب شد" && python app.py
cd ~/mvlite_bot && FILE="AAA_MVLITE_VOUCHER_ORDERS_PHASE08_$(date +%Y%m%d_%H%M%S).tar.gz" && tar -czf "/storage/emulated/0/Download/$FILE" . && echo "✅ /storage/emulated/0/Download/$FILE"
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_08_COMPLETE_ORDERS_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_08_COMPLETE_ORDERS_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Complete voucher orders phase 8"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_09_INVENTORY_SUPPLIERS_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_09_INVENTORY_SUPPLIERS_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add professional voucher inventory phase 9"
git push
cp ~/mvlite_bot/app.py /sdcard/Download/AAA_MVLITE_PHASE09_BEFORE_FINANCE.py
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_10_1_FINANCE_CORE_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_10_1_FINANCE_CORE_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add finance core phase 10.1"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_10_2_REPORTS_ALERTS_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_10_2_REPORTS_ALERTS_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add finance reports and alerts phase 10.2"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_10_3_ENTERPRISE_BI_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_10_3_ENTERPRISE_BI_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add enterprise BI dashboard phase 10.3"
git push
termux-setup-storage
cp /storage/emulated/0/Download/MVLITE_VOUCHER_PHASE_11_OPERATIONS_HARDENING_20260710.txt ~/
cd ~
bash MVLITE_VOUCHER_PHASE_11_OPERATIONS_HARDENING_20260710.txt
cd ~/mvlite_bot
git add .
git commit -m "Add operations and hardening phase 11"
git push
cd ~/mvlite_bot
python app.py
pkg install perl
cpan Term::Animation
curl -O https://www.robobunny.com/projects/asciiquarium/asciiquarium
chmod +x asciiquarium
perl asciiquarium
cd
pkg install neofetch
neofetch
pkg install aalib
aafire
pkg install pipes-sh
pipes.sh
pkg install nyancat
nyancat
pkg install gnuchess
gnuchess
clear
import io
import logging
import barcode
from barcode.writer import ImageWriter
from telegram import Update
from telegram.ext import (
)
# ===== تنظیمات =====
BOT_TOKEN = "YOUR_BOT_TOKEN"
logging.basicConfig(
)
# ==========================
# /start
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# ==========================
# ساخت بارکد
# ==========================
def create_barcode(data: str):
# ==========================
# دریافت پیام
# ==========================
async def message_handler(update: Update,
# ==========================
# اجرای ربات
# ==========================
def main():
pkg install unzip
pip install -r requirements.txt
cp /sdcard/Download/barcode_bot.zip ~/barcode_bot/
cd ~/barcode_bot
unzip barcode_bot.zip
mkdir -p ~/barcode_bot
cp /sdcard/Download/bot.py ~/barcode_bot/
cp /sdcard/Download/requirements.txt ~/barcode_bot/
cd ~/barcode_bot
pip install -r requirements.txt
nano bot.py
python bot.py
nano bot.py
python bot.py
vpn
pkg install python
pkg install python3
python3 sms.py 9172407062 --times 1000
python3 sms.py 9172407062 --times 5
pkg install phone
pkg update && pkg upgrade -y
pkg install openssh -y
ssh root@217.60.26.104
yes
ssh root@217.60.26.104
pkg update -y && pkg upgrade -y
pkg install python -y
pyTelegramBotAPI==4.14.0
pkg update -y
mkdir pishgam_bot
cd pishgam_bot
echo "pyTelegramBotAPI==4.14.0" > requirements.txt
pip install -r requirements.txt
cat << 'EOF' > main.py
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
EOF

python main.py
bash <(curl -Ls https://raw.githubusercontent.com/MhdiTaheri/sms-bomber/main/run.sh)
apt update -y && apt upgrade -y
pkg install git && pkg install python && pip install urllib3
git clone https://github.com/NiREvil/sms-bomber
cd sms-bomber
python sms-bomber.py
https://github.com/M-logique/Iran-Bomber/
cd rm
rm ~/sms_bomber/sms-bomber
git clone https://github.com/M-logique/Iran-Bomber/
cd Iran-Bomber
bash <(curl -Ls https://raw.githubusercontent.com/MhdiTaheri/sms-bomber/main/run.sh)
pip install requests fake-useragent
python BomberPlusV2.py
pkg install git
git clone
git clone https://github.com/esfelurm/sms_bomber.git
cd sms_bomber
python sms_bomber.py
cd ..
pip install mega.py
nano test_mega.py
python test_mega.py
cat << 'EOF' > test_mega.py
from mega import Mega

try:
    print("در حال اتصال به مگا...")
    mega = Mega()
    m = mega.login('nzriamirmhmd54@gmail.com', 'Amiramn0141+')
    
    quota = m.get_quota()
    print(f"✅ ورود موفقیت‌آمیز بود!")
    print(f"📊 میزان فضای مصرف شده: {quota} مگابایت")

except Exception as e:
    print(f"❌ خطا در اتصال به مگا: {e}")
EOF

python test_mega.py
# ۱. حذف نسخه قدیمی
pip uninstall mega.py tenacity -y
# ۲. نصب tenacity اصلاح شده و mega-py مدرن
pip install tenacity
pip install git+https://github.com/richardasgard/mega.py.git
# ۱. پاک کردن نسخه‌های قبلی که ارور می‌دادند
pip uninstall mega.py tenacity -y
# ۲. نصب مستقیم نسخه اصلاح‌شده و سازگار با پایتون جدید
pip install mega-py
cat << 'EOF' > test_mega.py
from mega import Mega

try:
    print("در حال اتصال به مگا...")
    mega = Mega()
    m = mega.login('nzriamirmhmd54@gmail.com', 'Amiramn0141+')
    
    print("✅ ورود موفقیت‌آمیز بود!")
    print("اکانت مگا با موفقیت متصل شد.")

except Exception as e:
    print(f"❌ خطا در اتصال به مگا: {e}")
EOF

python test_mega.py
pip uninstall mega.py mega-py tenacity -y
pkg install rclone -y
rclone config
n
rclone config
rclone config delete mymega
rclone config
rclone lsd mymega:
rclone config create mymega mega user nzriamirmhmd54@gmail.com pass Amiramn0141+
rclone lsd mymega:
