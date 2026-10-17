import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Cron-job এর জন্য হালকা সার্ভার (Keep-alive)
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
        return

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

# ৩০ মিনিট (১৮০০ সেকেন্ড) পর মেসেজ মুছে ফেলার ফাংশন
def auto_delete_messages(chat_id, message_ids, delay=1800):
    def delete_task():
        for mid in message_ids:
            try:
                bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass  # মেসেজ না থাকলে কোনো এরর হবে না
    
    # ব্যাকগ্রাউন্ডে ৩০ মিনিটের টাইমার চালু
    threading.Timer(delay, delete_task).start()

# চ্যানেলে ভিডিও দিলে লিংক তৈরি করবে
@bot.channel_post_handler(content_types=['video', 'document', 'audio', 'photo'])
def on_channel_post(message):
    global CHANNEL_ID
    CHANNEL_ID = message.chat.id
    
    msg_id = message.message_id
    me = bot.get_me()
    share_link = f"https://t.me/{me.username}?start=file_{msg_id}"
    bot.send_message(message.chat.id, f"✅ New video link generated:\n\n{share_link}")

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
                
                # মেসেজ পাঠানো (৩০ মিনিটের নোটিশ সহ)
                msg_text = bot.send_message(
                    message.chat.id, 
                    "🎉 Ad verified! Here is your video.\n\n⏳ Note: This video will be automatically deleted in 30 minutes."
                )
                
                # ফুল সিকিউরিটিতে ভিডিও কপি করা (ডাউনলোড/ফরওয়ার্ড বন্ধ)
                msg_video = bot.copy_message(
                    chat_id=message.chat.id, 
                    from_chat_id=CHANNEL_ID, 
                    message_id=file_id, 
                    protect_content=True
                )
                
                # ঠিক ৩০ মিনিট (১৮০০ সেকেন্ড) পর মেসেজ ও ভিডিও ডিলিট হয়ে যাবে
                auto_delete_messages(
                    chat_id=message.chat.id, 
                    message_ids=[msg_text.message_id, msg_video.message_id], 
                    delay=1800
                )
            else:
                bot.send_message(message.chat.id, "⚠️ No video found. Please use the link from the channel.")
            return

        # ইউজার ভিডিও লিংকে ক্লিক করে আসলে
        if param.startswith("file_"):
            file_id = param.replace("file_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?file={file_id}"
            markup.add(InlineKeyboardButton("🎬 Watch Ad to Unlock Video", web_app=WebAppInfo(url=app_url)))
            bot.send_message(message.chat.id, "Click the button below and watch the full ad to unlock the video:", reply_markup=markup)
            return

    bot.send_message(message.chat.id, "👋 Hello! You cannot watch videos directly here.\nPlease click the specific video link from our channel to unlock and watch.")

bot.infinity_polling()
