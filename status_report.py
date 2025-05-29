import time
import telebot
from datetime import datetime

TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
CHAT_ID = '230315107'
bot = telebot.TeleBot(TOKEN)

def send_status():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"🟢 البوت يعمل الآن بشكل طبيعي ✅\n⏰ الوقت: {now}\n📊 سيتم إرسال توصية تلقائيًا عند توفر شروط السوق."
    bot.send_message(CHAT_ID, message)
    print("[STATUS] رسالة حالة مرسلة.")

def start_status_report():
    while True:
        send_status()
        time.sleep(3600)