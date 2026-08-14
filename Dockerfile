FROM python:3.11-slim

RUN apt-get update && apt-get install -y rclone curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# اضافه کردن این بخش برای اینکه خروجی‌ها در ریل‌وی بلافاصله چاپ بشن
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
