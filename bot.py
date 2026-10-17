import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Keep-alive সার্ভার (Render কে ২৪ ঘণ্টা সচল রাখার জন্য)
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

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBAPP_URL = os.environ.get('WEBAPP_URL', '')

bot = telebot.TeleBot(BOT_TOKEN)

# নির্দিষ্ট সময় পর মেসেজ মুছে ফেলার ফাংশন
def auto_delete_messages(chat_id, message_ids, delay=150):
    def delete_task():
        for mid in message_ids:
            try:
                bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass  # মেসেজ না থাকলে কোনো এরর হবে না
    
    # ব্যাকগ্রাউন্ডে টাইমার চালু (ডিফল্ট: ৫ মিনিট / ৩০০ সেকেন্ড)
    threading.Timer(delay, delete_task).start()

# চ্যানেলে Catbox লিংক দিলে প্লেয়ার লিংক তৈরি করবে
@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
def on_channel_text(message):
    text = message.text or message.caption or ""
    match = re.search(r'catbox\.moe/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if match:
        raw_code = match.group(1)
        video_code = re.sub(r'\.(mp4|MP4|mkv|mov)$', '', raw_code)
        me = bot.get_me()
        share_link = f"https://t.me/{me.username}?start=v_{video_code}"
        bot.send_message(message.chat.id, f"✅ New Secure Player Link:\n\n{share_link}")

@bot.message_handler(commands=['start'])
def on_start(message):
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        # ইউজার ভিডিও লিংকে ক্লিক করে আসলে
        if param.startswith("v_"):
            video_code = param.replace("v_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?v={video_code}"
            
            markup.add(InlineKeyboardButton("🎬 Watch Video (Protected Player)", web_app=WebAppInfo(url=app_url)))
            
            # বাটনসহ মেসেজ পাঠানো
            sent_msg = bot.send_message(
                message.chat.id, 
                "Click the button below to watch the video in our secure in-app player:\n\n⏳ (This button will disappear in 5 minutes)", 
                reply_markup=markup
            )
            
            # ঠিক ৫ মিনিট (৩০০ সেকেন্ড) পর ইউজারের /start মেসেজ এবং বটের বাটন দুটোই স্বয়ংক্রিয়ভাবে মুছে যাবে
            auto_delete_messages(
                chat_id=message.chat.id, 
                message_ids=[message.message_id, sent_msg.message_id], 
                delay=300
            )
            return

    bot.send_message(message.chat.id, "👋 Hello! Please open any video link from our channel to watch in our secure player.")

bot.infinity_polling()
