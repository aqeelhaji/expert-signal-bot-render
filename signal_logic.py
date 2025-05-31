
import requests
import pandas as pd
import telebot
import datetime
import time
import threading

# إعدادات TwelveData API
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
EURUSD_URL = f'https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&apikey={API_KEY}&outputsize=100'
GOLD_URL = f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100'

# توكنات تيليجرام لكل بوت
EUR_BOT = telebot.TeleBot('8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE')
GOLD_BOT = telebot.TeleBot('7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME')

# الشات
EUR_CHAT_ID = '230315107'
GOLD_CHAT_ID = '230315107'

def send_signal(pair, signal, bot, chat_id):
    message = f"توصية جديدة لـ {pair}:\n✅ {signal}\n⏱️ نفّذ الصفقة بفريم 1:30 دقيقة"
    bot.send_message(chat_id, message)
    print(message)

def send_hourly_status(bot, chat_id, label):
    while True:
        now = datetime.datetime.now().strftime('%H:%M:%S')
        message = f"[{label}] البوت يعمل ✅ الساعة الآن: {now}"
        bot.send_message(chat_id, message)
        time.sleep(3600)

def calculate_indicators(df):
    df['close'] = df['close'].astype(float)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['sma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper_band'] = df['sma'] + 2 * df['std']
    df['lower_band'] = df['sma'] - 2 * df['std']
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df

def analyze_market(pair, url, bot, chat_id):
    while True:
        try:
            response = requests.get(url)
            data = response.json()
            if 'values' not in data:
                print(f"❌ فشل في جلب البيانات لـ {pair}")
            else:
                df = pd.DataFrame(data['values'])
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.sort_values('datetime')
                df = calculate_indicators(df)
                latest = df.iloc[-1]
                buy = latest['rsi'] < 30 and latest['close'] < latest['lower_band'] and latest['macd'] > latest['macd_signal']
                sell = latest['rsi'] > 70 and latest['close'] > latest['upper_band'] and latest['macd'] < latest['macd_signal']
                if buy:
                    send_signal(pair, "شراء", bot, chat_id)
                elif sell:
                    send_signal(pair, "بيع", bot, chat_id)
                else:
                    print(f"[{pair}] لا توجد توصية حالياً...")
        except Exception as e:
            print(f"[{pair}] خطأ: {e}")
        time.sleep(60)

def run_bots():
    threading.Thread(target=analyze_market, args=('EUR/USD', EURUSD_URL, EUR_BOT, EUR_CHAT_ID)).start()
    threading.Thread(target=analyze_market, args=('XAU/USD', GOLD_URL, GOLD_BOT, GOLD_CHAT_ID)).start()
    threading.Thread(target=send_hourly_status, args=(EUR_BOT, EUR_CHAT_ID, 'EUR/USD')).start()
    threading.Thread(target=send_hourly_status, args=(GOLD_BOT, GOLD_CHAT_ID, 'XAU/USD')).start()
