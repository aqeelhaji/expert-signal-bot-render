
import requests
import pandas as pd
import datetime
import telebot
import time

# إعدادات TwelveData API
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
EURUSD_URL = f'https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&apikey={API_KEY}&outputsize=100'
GOLD_URL = f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100'

# إعدادات تيليجرام
EURUSD_TOKEN = '8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE'
GOLD_TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
CHAT_ID = '230315107'
eurusd_bot = telebot.TeleBot(EURUSD_TOKEN)
gold_bot = telebot.TeleBot(GOLD_TOKEN)

last_status_time = {
    "EUR/USD": 0,
    "XAU/USD": 0
}

def send_signal(pair, signal):
    message = f"📊 توصية جديدة لـ {pair}:\n✅ {signal}\n⏱️ نفّذ الصفقة بفريم 1:30 دقيقة"
    if pair == "EUR/USD":
        eurusd_bot.send_message(CHAT_ID, message)
    else:
        gold_bot.send_message(CHAT_ID, message)
    print(message)

def send_hourly_status(pair):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    message = f"⏱️ البوت يعمل لـ {pair} ✅ الساعة: {now}"
    if pair == "EUR/USD":
        eurusd_bot.send_message(CHAT_ID, message)
    else:
        gold_bot.send_message(CHAT_ID, message)

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

def analyze_market(pair):
    url = EURUSD_URL if pair == 'EUR/USD' else GOLD_URL
    response = requests.get(url)
    data = response.json()
    if 'values' not in data:
        print(f"❌ فشل في جلب البيانات لـ {pair}")
        return None
    df = pd.DataFrame(data['values'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    conditions_met = 0
    if latest['rsi'] < 30 or latest['rsi'] > 70:
        conditions_met += 1
    if latest['close'] < latest['lower_band'] or latest['close'] > latest['upper_band']:
        conditions_met += 1
    if (latest['macd'] > latest['macd_signal']) or (latest['macd'] < latest['macd_signal']):
        conditions_met += 1
    if conditions_met >= 3:
        return "شراء" if latest['rsi'] < 30 else "بيع"
    elif conditions_met == 2:
        return "🚨 توصية محتملة (شرطان متحققان)"
    else:
        return None

def run_bots():
    while True:
        for pair in ["EUR/USD", "XAU/USD"]:
            try:
                signal = analyze_market(pair)
                if signal:
                    send_signal(pair, signal)
                # إرسال حالة البوت كل ساعة
                if time.time() - last_status_time[pair] > 3600:
                    send_hourly_status(pair)
                    last_status_time[pair] = time.time()
            except Exception as e:
                print(f"⚠️ خطأ في {pair}: {e}")
        time.sleep(60)
