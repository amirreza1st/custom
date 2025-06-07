import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
from dotenv import load_dotenv
import openai  # اضافه شد برای هوش مصنوعی

load_dotenv()  # بارگذاری متغیرهای محیطی از .env

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # کلید اوپن ای آی

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

openai.api_key = OPENAI_API_KEY

user_states = {}
reply_states = {}

def start_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("HiddenChat 👀", callback_data="anon_msg"),
        InlineKeyboardButton("PlayList 🎧", callback_data="playlist"),
        InlineKeyboardButton("Links ☄️", callback_data="links"),
        InlineKeyboardButton("Channel 🩸", url="https://t.me/anoraorg"),
        InlineKeyboardButton("شروع چت زنده 🤖", callback_data="start_chat")  # دکمه جدید
    )
    return markup

def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("بـســتن", callback_data="cancel"))
    return markup

def admin_reply_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Answer", callback_data=f"reply_{user_id}"),
        InlineKeyboardButton("Block", callback_data=f"block_{user_id}"),
        InlineKeyboardButton("Divert", callback_data=f"ignore_{user_id}")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """ســلام ، من امیررضـام .🦇

خــــوش اومـدی ❣""", reply_markup=start_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data == "anon_msg":
        user_states[call.from_user.id] = "anon"
        bot.send_message(call.message.chat.id,
                         """هر پیامی که از الان بفرستی به صورت ناشناس برای مــن ارسال میشــه 👐

هروقت تموم شد روی "بـســتن" کلیک کن 🙌""",
                         reply_markup=cancel_keyboard())
    elif data == "cancel":
        if user_states.get(call.from_user.id) == "chatting":
            user_states.pop(call.from_user.id, None)
            bot.send_message(call.message.chat.id, "چت زنده متوقف شد.", reply_markup=start_keyboard())
        else:
            user_states.pop(call.from_user.id, None)
            bot.send_message(call.message.chat.id, "پنــل ناشـناس بستـه شــد")
    elif data == "playlist":
        bot.send_message(call.message.chat.id, """🎧 Listen to "SaVaGe" on #SoundCloud

https://on.soundcloud.com/28yny4Qd4ThYAPGcWt
""")
    elif data == "links":
        bot.send_message(call.message.chat.id, """Links 💋

— TelG ›››
https://t.me/rewhi

- Insta ›››
https://www.instagram.com/amirrezkhalili?igsh=aHVteG91NWZtb3V6

· SoundCloud ›››
https://on.soundcloud.com/GA0YwIlCeV9DyNQsfA
""")
    elif data == "start_chat":  # شروع چت زنده
        user_states[call.from_user.id] = "chatting"
        bot.send_message(call.message.chat.id, "ربات حاضر است، هر چی می‌خوای بگو!", reply_markup=cancel_keyboard())
    elif data.startswith("reply_"):
        target_user = int(data.split("_")[1])
        reply_states[call.from_user.id] = target_user
        bot.send_message(call.message.chat.id, "✍️ Benevis ta befrestam.")
    elif data.startswith("block_"):
        blocked_user = int(data.split("_")[1])
        bot.send_message(call.message.chat.id, f"❌ user {blocked_user} block shod.")
    elif data.startswith("ignore_"):
        bot.send_message(call.message.chat.id, "⏳ divert shod.")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "anon")
def handle_anon_message(message):
    sender = message.from_user
    user_info = f"👤 from: {sender.first_name}"
    if sender.username:
        user_info += f"\n📎 username: @{sender.username}"
    user_info += f"\n🆔 number id: {sender.id}"
    msg = f"{user_info}\n\n📨 payam:\n{message.text}"
    bot.send_message(ADMIN_ID, msg, reply_markup=admin_reply_keyboard(sender.id))
    bot.send_message(message.chat.id, """پیامــــت ارسال شد عزیــزم .🧸
منتظــر باش تا از همیــنجا جوابت رو بــدم""")
    user_states.pop(message.from_user.id, None)

import traceback

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "chatting")
def live_chat_handler(message):
    user_msg = message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "تو یک دستیار فارسی هستی."},
                {"role": "user", "content": user_msg}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        bot_reply = response['choices'][0]['message']['content'].strip()
        bot.send_message(message.chat.id, bot_reply)
    except Exception as e:
        bot.send_message(message.chat.id, "متاسفانه در پاسخ‌دهی به مشکل خوردیم. لطفا دوباره تلاش کن.")
        print("OpenAI API error:", e)
        traceback.print_exc()


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.chat.type == "private")
def handle_admin_reply(message):
    if message.from_user.id in reply_states:
        target_id = reply_states.pop(message.from_user.id)
        bot.send_message(target_id, f"{message.text}\n\n✍️ Sign by Amirreza")
        bot.send_message(message.chat.id, "✅ sended.")

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
