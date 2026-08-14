FROM alpine:3.19

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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages

COPY . .

# اجرای ایمن سرور محلی با آرگومان‌های کامل
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'mkdir -p /app/tg-data /app/tg-temp' >> /app/entrypoint.sh && \
    echo '/usr/local/bin/telegram-bot-api --api-id=6 --api-hash=eb06d4abfb49dc3eeb1aeb9890f1 --local --http-port=8081 --dir=/app/tg-data --temp-dir=/app/tg-temp &' >> /app/entrypoint.sh && \
    echo 'sleep 4' >> /app/entrypoint.sh && \
    echo 'python3 bot.py' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
