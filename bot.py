import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))
WEBAPP_URL = os.environ.get('WEBAPP_URL')

bot = telebot.TeleBot(BOT_TOKEN)

# প্রাইভেট চ্যানেলে ভিডিও আপলোড করলে বট লিংক বানিয়ে দেবে
@bot.channel_post_handler(content_types=['video', 'document', 'audio'])
def on_channel_post(message):
    if message.chat.id == CHANNEL_ID:
        msg_id = message.message_id
        me = bot.get_me()
        share_link = f"https://t.me/{me.username}?start=file_{msg_id}"
        bot.reply_to(message, f"✅ ভিডিওর লিংক তৈরি হয়েছে:\n\n{share_link}")

# ইউজার লিংকে ক্লিক করে বটে আসলে
@bot.message_handler(commands=['start'])
def on_start(message):
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        # ইউজার এড দেখে ফেরত আসলে ভিডিও পাঠিয়ে দেবে
        if param.startswith("unlock_"):
            file_id = int(param.replace("unlock_", ""))
            bot.send_message(message.chat.id, "🎉 এড দেখা সফল হয়েছে! এই নিন আপনার ভিডিও:")
            bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=file_id)
            return

        # ইউজার ভিডিওর লিংকে প্রথমবার ক্লিক করলে
        if param.startswith("file_"):
            file_id = param.replace("file_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?file={file_id}"
            
            # এড দেখার মিনি অ্যাপ বাটন
            markup.add(InlineKeyboardButton("🎬 এড দেখে ভিডিও খুলুন", web_app=WebAppInfo(url=app_url)))
            bot.send_message(message.chat.id, "ভিডিওটি দেখতে নিচের বাটনে ক্লিক করে এডটি দেখুন:", reply_markup=markup)
            return

    bot.send_message(message.chat.id, "ভিডিও পেতে চ্যানেলের নির্দিষ্ট লিংকে ক্লিক করুন।")

bot.infinity_polling()
