FROM python:3.10-slim

# نصب ffmpeg و سایر پیش‌نیازها
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# نصب پکیج‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن بقیه فایل‌ها
COPY . .

# ست کردن پورت و اجرای برنامه
ENV PORT=5000
CMD ["python", "bot.py"]
