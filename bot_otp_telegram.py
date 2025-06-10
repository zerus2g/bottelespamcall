import os
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from s1 import otp_services
from flask import Flask

# Hàm xử lý lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Chào bạn! Gửi /spam <sdt> <số lần> để bắt đầu spam OTP.")

# Hàm xử lý lệnh /spam
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        phone = context.args[0]
        count = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Cú pháp: /spam <sdt> <số lần>")
        return

    await update.message.reply_text(f"Bắt đầu spam OTP tới {phone} ({count} lần)...")
    for i in range(count):
        results = {}
        threads = []
        def wrapper(service):
            try:
                service(phone)
                results[service.__name__] = True
            except Exception:
                results[service.__name__] = False
        for service in otp_services:
            t = threading.Thread(target=wrapper, args=(service,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        # Gửi kết quả từng lần
        msg = f"Lần {i+1}:\n"
        for name, status in results.items():
            service_name = name.replace('send_otp_via_', '')
            if status:
                state = "✅ Thành công"
            else:
                state = "❌ Thất bại"
            msg += f"- {service_name}: {state}\n"
        await update.message.reply_text(msg)
    await update.message.reply_text("Đã hoàn thành gửi OTP!")

# Tạo Flask app
flask_app = Flask(__name__)

@flask_app.route('/ping')
def ping():
    return "pong", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    # Đọc token từ biến môi trường
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    # Chạy Flask ở thread riêng
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Chạy bot Telegram
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spam", spam))
    app.run_polling() 