FROM python:3.11-slim

RUN apt-get update && apt-get install -y rclone curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir python-telegram-bot

# این خط جادویی مانع بسته شدن کانتینر میشه
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
