FROM alpine:3.19

# نصب پایتون، Rclone و پیش‌نیازها
RUN apk add --no-cache \
    python3 \
    py3-pip \
    rclone \
    curl \
    ca-certificates \
    bash

# دانلود باینری رسمی Telegram Bot API Server
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -L -o /usr/local/bin/telegram-bot-api https://github.com/aiogram/telegram-bot-api-binaries/releases/latest/download/telegram-bot-api-linux-amd64 ; \
    else \
        curl -L -o /usr/local/bin/telegram-bot-api https://github.com/aiogram/telegram-bot-api-binaries/releases/latest/download/telegram-bot-api-linux-arm64 ; \
    fi && \
    chmod +x /usr/local/bin/telegram-bot-api

WORKDIR /app

# نصب کتابخانه‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

COPY . .

# اسکریپت اجرای همزمان سرور تلگرام و ربات
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo '/usr/local/bin/telegram-bot-api --local --http-port=8081 --dir=/app/tg-data --temp-dir=/app/tg-temp &' >> /app/entrypoint.sh && \
    echo 'sleep 2' >> /app/entrypoint.sh && \
    echo 'python3 bot.py' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
