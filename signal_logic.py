import requests
import pandas as pd
import datetime
import telebot
import time

# إعدادات TwelveData API
API_KEY = "dd98455cbb9b4161b38d5d8e561b5f72"
EURUSD_URL = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&apikey={API_KEY}&outputsize=100"
GOLD_URL = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100"

# توكنات البوتات
EURUSD_BOT_TOKEN = "8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE"
GOLD_BOT_TOKEN = "7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME"
CHAT_ID = "230315107"

eurusd_bot = telebot.TeleBot(EURUSD_BOT_TOKEN)
gold_bot = telebot.TeleBot(GOLD_BOT_TOKEN)

last_hour_alert = {"EUR/USD": None, "XAU/USD": None}

def send_signal(pair, signal, bot):
    message = f"📊 توصية جديدة لـ {pair}:
✅ {signal}
⏱️ نفّذ الصفقة بفريم 1:30 دقيقة"
    bot.send_message(CHAT_ID, message)
    print(message)

def send_hourly_status(pair, bot):
    now = datetime.datetime.now()
    if last_hour_alert[pair] is None or (now - last_hour_alert[pair]).seconds >= 3600:
        last_hour_alert[pair] = now
        message = f"⏱️ البوت يعمل ✅ {pair} الساعة الآن: {now.strftime('%H:%M:%S')}"
        bot.send_message(CHAT_ID, message)

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

def analyze_market(url, pair, bot):
    try:
        response = requests.get(url)
        data = response.json()
        if "values" not in data:
            print(f"❌ فشل في جلب البيانات لـ {pair}")
            return None
        df = pd.DataFrame(data["values"])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        buy = latest['rsi'] < 30 and latest['close'] < latest['lower_band'] and latest['macd'] > latest['macd_signal']
        sell = latest['rsi'] > 70 and latest['close'] > latest['upper_band'] and latest['macd'] < latest['macd_signal']
        if buy:
            return "شراء"
        elif sell:
            return "بيع"
    except Exception as e:
        print(f"⚠️ خطأ في {pair}: {e}")
    return None

def run_bots():
    while True:
        eurusd_signal = analyze_market(EURUSD_URL, "EUR/USD", eurusd_bot)
        gold_signal = analyze_market(GOLD_URL, "XAU/USD", gold_bot)

        if eurusd_signal:
            send_signal("EUR/USD", eurusd_signal, eurusd_bot)
        if gold_signal:
            send_signal("XAU/USD", gold_signal, gold_bot)

        send_hourly_status("EUR/USD", eurusd_bot)
        send_hourly_status("XAU/USD", gold_bot)

        time.sleep(60)