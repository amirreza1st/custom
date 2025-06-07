import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
from dotenv import load_dotenv

load_dotenv()  # بارگذاری متغیرهای محیطی از .env

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_states = {}
reply_states = {}

def start_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("پیام ناشناس به امیررضا", callback_data="anon_msg"),
        InlineKeyboardButton("پلی لیست امیررضا", callback_data="playlist"),
        InlineKeyboardButton("لینک‌های امیررضا", callback_data="links"),
        InlineKeyboardButton("اینستا", url="https://instagram.com/amirreza")
    )
    return markup

def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("انصراف", callback_data="cancel"))
    return markup

def admin_reply_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✍️ پاسخ دادن", callback_data=f"reply_{user_id}"),
        InlineKeyboardButton("🚫 بلاک کردن", callback_data=f"block_{user_id}"),
        InlineKeyboardButton("❌ نادیده گرفتن", callback_data=f"ignore_{user_id}")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "سلام! خوش اومدی 🌟 یکی از گزینه‌های زیر رو انتخاب کن:", reply_markup=start_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data == "anon_msg":
        user_states[call.from_user.id] = "anon"
        bot.send_message(call.message.chat.id,
                         "📨 هر پیامی که اینجا ارسال کنی به صورت ناشناس برای امیررضا فرستاده میشه. برای انصراف روی دکمه زیر بزن.",
                         reply_markup=cancel_keyboard())
    elif data == "cancel":
        user_states.pop(call.from_user.id, None)
        bot.send_message(call.message.chat.id, "❌ ارسال پیام ناشناس لغو شد.")
    elif data == "playlist":
        bot.send_message(call.message.chat.id, "🎵 پلی‌لیست امیررضا:")
        bot.send_audio(call.message.chat.id, open("music1.mp3", "rb"))
        bot.send_audio(call.message.chat.id, open("music2.mp3", "rb"))
        bot.send_message(call.message.chat.id, "📄 توضیحات: این آهنگ‌ها مورد علاقه‌ٔ امیررضا هستن.")
    elif data == "links":
        bot.send_message(call.message.chat.id, "🔗 لینک‌های امیررضا:\n- سایت: https://amirreza.me\n- کانال: https://t.me/example")
    elif data.startswith("reply_"):
        target_user = int(data.split("_")[1])
        reply_states[call.from_user.id] = target_user
        bot.send_message(call.message.chat.id, "✍️ لطفاً پاسخ خودت رو بنویس. این پیام برای کاربر فرستاده میشه.")
    elif data.startswith("block_"):
        blocked_user = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, f"❌ کاربر {blocked_user} بلاک شد (عملیاتی انجام نشد).")
    elif data.startswith("ignore_"):
        bot.send_message(call.message.chat.id, "⏳ نادیده گرفته شد.")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "anon")
def handle_anon_message(message):
    sender = message.from_user
    user_info = f"👤 پیام از: {sender.first_name}"
    if sender.username:
        user_info += f"\n📎 یوزرنیم: @{sender.username}"
    user_info += f"\n🆔 آیدی عددی: {sender.id}"
    msg = f"{user_info}\n\n📨 پیام:\n{message.text}"
    bot.send_message(ADMIN_ID, msg, reply_markup=admin_reply_keyboard(sender.id))
    bot.send_message(message.chat.id, "✅ پیام شما با موفقیت ارسال شد.")
    user_states.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.chat.type == "private")
def handle_admin_reply(message):
    if message.from_user.id in reply_states:
        target_id = reply_states.pop(message.from_user.id)
        bot.send_message(target_id, f"{message.text}\n\n✍️ کوچیک شما, امیررضا")
        bot.send_message(message.chat.id, "✅ پاسخ شما برای کاربر ارسال شد.")

# Webhook route برای Railway
@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running.", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
