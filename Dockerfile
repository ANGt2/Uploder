FROM python:3.11-slim

# نصب rclone و ابزارهای مورد نیاز
RUN apt-get update && apt-get install -y rclone curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# کپی کردن تمام فایل‌های پوشه
COPY . .

# نصب مستقیم کتابخانه تلگرام
RUN pip install --no-cache-dir python-telegram-bot

# اجرای ربات
CMD ["python", "bot.py"]
