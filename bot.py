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

# চ্যানেলে যেকোনো ফরম্যাটে Catbox লিংক দিলে ধরে ফেলবে
@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
def on_channel_text(message):
    text = message.text or message.caption or ""
    
    # Catbox লিংক নিখুঁতভাবে শনাক্ত করার শক্তিশালী ফিল্টার
    match = re.search(r'catbox\.moe/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
    if match:
        raw_code = match.group(1)
        # .mp4 বা বাড়তি অংশ মুছে শুধু কোড আলাদা করা
        video_code = re.sub(r'\.(mp4|MP4|mkv|mov)$', '', raw_code)
        
        me = bot.get_me()
        share_link = f"https://t.me/{me.username}?start=v_{video_code}"
        bot.send_message(message.chat.id, f"✅ New Secure Player Link:\n\n{share_link}")

@bot.message_handler(commands=['start'])
def on_start(message):
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        
        if param.startswith("v_"):
            video_code = param.replace("v_", "")
            markup = InlineKeyboardMarkup()
            app_url = f"{WEBAPP_URL}?v={video_code}"
            
            markup.add(InlineKeyboardButton("🎬 Watch Video (Protected Player)", web_app=WebAppInfo(url=app_url)))
            bot.send_message(
                message.chat.id, 
                "Click the button below to watch the video in our secure in-app player:", 
                reply_markup=markup
            )
            return

    bot.send_message(message.chat.id, "👋 Hello! Please open any video link from our channel to watch in our secure player.")

bot.infinity_polling()
