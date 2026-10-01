import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Render এর ফ্রি সার্ভার চালু রাখার জন্য ছোট একটি ফেক সার্ভার
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

# সার্ভার চালু হলো
threading.Thread(target=run_server, daemon=True).start()

# টেলিগ্রাম বট কোড
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))
WEBAPP_URL = os.environ.get('WEBAPP_URL')

bot = telebot.TeleBot(BOT_TOKEN)

@bot.channel_post_handler(content_types=['video', 'document', 'audio'])
def on_channel_post(message):
    if message.chat.id == CHANNEL_ID:
        msg_id = message.message_id
        me = bot.get_me()
        share_link = f"https://t.me/{me.username}?start=file_{msg_id}"
        bot.reply_to(message, f"✅ ভিডিওর লিংক তৈরি হয়েছে:\n\n{share_link}")

@bot.message_handler(commands=['start'])
def on_start(message):
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        if param.startswith("unlock_"):
            file_id = int(param.replace("unlock_", ""))
            bot.send_message(message.chat.id, "🎉 এড দেখা সফল হয়েছে! এই নিন আপনার ভিডিও:")
            bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=file_id)
            return

        if param.startswith("file_"):
            file_id = param.replace("file_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?file={file_id}"
            
            markup.add(InlineKeyboardButton("🎬 এড দেখে ভিডিও খুলুন", web_app=WebAppInfo(url=app_url)))
            bot.send_message(message.chat.id, "ভিডিওটি দেখতে নিচের বাটনে ক্লিক করে এডটি দেখুন:", reply_markup=markup)
            return

    bot.send_message(message.chat.id, "ভিডিও পেতে চ্যানেলের নির্দিষ্ট লিংকে ক্লিক করুন।")

bot.infinity_polling()
