from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def phone_menu():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 اشتراک شماره تلفن", request_contact=True)]],
        resize_keyboard=True
    )


def main_menu():
    return ReplyKeyboardMarkup([
        ["🛒 خرید Uvoucher"],
        ["👤 حساب کاربری", "💰 کیف پول"],
        ["📦 سفارشات من", "🎫 کدهای خریداری شده"],
        ["📞 پشتیبانی", "📖 راهنما"],
    ], resize_keyboard=True)


def profile_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪪 احراز هویت", callback_data="user_kyc")],
        [InlineKeyboardButton("📦 سفارشات من", callback_data="user_orders")],
    ])


def admin_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 سفارش‌های در انتظار", callback_data="admin_pending")],
        [InlineKeyboardButton("📦 آخرین سفارش‌ها", callback_data="admin_orders")],
        [InlineKeyboardButton("👥 کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("🪪 احرازها", callback_data="admin_kyc")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")],
    ])
