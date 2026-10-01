import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Render এর ফ্রি সার্ভার সচল রাখার ফেক সার্ভার
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# পরিবেশ ভেরিয়েবল নেওয়া
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', '0'))
WEBAPP_URL = os.environ.get('WEBAPP_URL', '')

bot = telebot.TeleBot(BOT_TOKEN)

# প্রাইভেট চ্যানেলে ভিডিও, ফাইল বা ছবি দিলে সাথে সাথে লিংক তৈরি করবে
@bot.channel_post_handler(content_types=['video', 'document', 'audio', 'photo'])
def on_channel_post(message):
    if message.chat.id == CHANNEL_ID:
        msg_id = message.message_id
        me = bot.get_me()
        share_link = f"https://t.me/{me.username}?start=file_{msg_id}"
        # চ্যানেলে সরাসরি মেসেজ পাঠাবে
        bot.send_message(CHANNEL_ID, f"✅ নতুন ভিডিওর লিংক তৈরি হয়েছে:\n\n{share_link}")

# ইউজার লিংকে ক্লিক করলে
@bot.message_handler(commands=['start'])
def on_start(message):
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        # ইউজার এড দেখে ফেরত আসলে
        if param.startswith("unlock_"):
            raw_id = param.replace("unlock_", "")
            if raw_id.isdigit():
                file_id = int(raw_id)
                bot.send_message(message.chat.id, "🎉 এড দেখা সফল হয়েছে! এই নিন আপনার ভিডিও:")
                bot.copy_message(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=file_id)
            else:
                bot.send_message(message.chat.id, "⚠️ কোনো নির্দিষ্ট ভিডিও পাওয়া যায়নি। চ্যানেলের লিংক থেকে আসুন।")
            return

        # ইউজার চ্যানেলের ভিডিও লিংকে ক্লিক করে আসলে
        if param.startswith("file_"):
            file_id = param.replace("file_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?file={file_id}"
            
            markup.add(InlineKeyboardButton("🎬 এড দেখে ভিডিও খুলুন", web_app=WebAppInfo(url=app_url)))
            bot.send_message(message.chat.id, "ভিডিওটি দেখতে নিচের বাটনে ক্লিক করে এডটি সম্পূর্ণ দেখুন:", reply_markup=markup)
            return

    # সাধারণ /start দিলে এই মেসেজ আসবে
    bot.send_message(message.chat.id, "👋 হ্যালো! বটটি সম্পূর্ণ সচল আছে।\nআপনার প্রাইভেট চ্যানেলে ভিডিও আপলোড করুন, বট স্বয়ংক্রিয়ভাবে ভিডিওর লিংক তৈরি করে দেবে।")

bot.infinity_polling()
