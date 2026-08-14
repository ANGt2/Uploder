FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl unzip ca-certificates && \
    curl https://rclone.org/install.sh | bash && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir python-telegram-bot

ENV PYTHONUNBUFFERED=1
ENV RCLONE_CONFIG=/app/rclone.conf

CMD ["python", "bot.py"]
