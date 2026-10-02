import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Cron-job এর জন্য অতি হালকা রেসপন্স (যাতে output too large এরর না আসে)
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return  # অতিরিক্ত লগ বন্ধ

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# এনভায়রনমেন্ট ভেরিয়েবল
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBAPP_URL = os.environ.get('WEBAPP_URL', '')
raw_channel_id = os.environ.get('CHANNEL_ID', '0')
CHANNEL_ID = int(raw_channel_id) if raw_channel_id and raw_channel_id != 'null' else 0

bot = telebot.TeleBot(BOT_TOKEN)

# চ্যানেলে ভিডিও/ফাইল/ছবি দিলে সাথে সাথে লিংক তৈরি করবে
@bot.channel_post_handler(content_types=['video', 'document', 'audio', 'photo'])
def on_channel_post(message):
    global CHANNEL_ID
    CHANNEL_ID = message.chat.id  # স্বয়ংক্রিয়ভাবে আসল চ্যানেল আইডি ধরে নেবে
    
    msg_id = message.message_id
    me = bot.get_me()
    share_link = f"https://t.me/{me.username}?start=file_{msg_id}"
    bot.send_message(message.chat.id, f"✅ নতুন ভিডিওর লিংক তৈরি হয়েছে:\n\n{share_link}")

@bot.message_handler(commands=['start'])
def on_start(message):
    global CHANNEL_ID
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

        # ইউজার ভিডিও লিংকে ক্লিক করে আসলে
        if param.startswith("file_"):
            file_id = param.replace("file_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?file={file_id}"
            markup.add(InlineKeyboardButton("🎬 এড দেখে ভিডিও খুলুন", web_app=WebAppInfo(url=app_url)))
            bot.send_message(message.chat.id, "ভিডিওটি দেখতে নিচের বাটনে ক্লিক করে এডটি সম্পূর্ণ দেখুন:", reply_markup=markup)
            return

    bot.send_message(message.chat.id, "👋 হ্যালো! বট সম্পূর্ণ সচল আছে। চ্যানেলে ভিডিও ছাড়লে লিংক তৈরি হবে।")

bot.infinity_polling()
