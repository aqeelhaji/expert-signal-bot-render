
import requests
import pandas as pd
import telebot
import datetime
import time

# Telegram Settings
TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
CHAT_ID = '230315107'
bot = telebot.TeleBot(TOKEN)

# TwelveData API
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
EURUSD_URL = f'https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&apikey={API_KEY}&outputsize=100'
GOLD_URL = f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100'

last_hour_notified = None

def send_signal(pair, signal):
    message = f"📊 توصية جديدة لـ {pair}:
✅ {signal}
⏱️ نفّذ الصفقة بفريم {'30 ثانية' if pair == 'EUR/USD' else '1:30 دقيقة'}"
    bot.send_message(CHAT_ID, message)
    print(message)

def send_hourly_status():
    global last_hour_notified
    now = datetime.datetime.now()
    if not last_hour_notified or (now - last_hour_notified).seconds >= 3600:
        last_hour_notified = now
        status = f"⏱️ البوت يعمل ✅ الساعة الآن: {now.strftime('%H:%M:%S')}"
        bot.send_message(CHAT_ID, status)

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

    buy = (latest['rsi'] < 35 and latest['close'] < latest['lower_band']) or (latest['macd'] > latest['macd_signal'])
    sell = (latest['rsi'] > 65 and latest['close'] > latest['upper_band']) or (latest['macd'] < latest['macd_signal'])

    if buy:
        return "شراء"
    elif sell:
        return "بيع"
    else:
        return None

def run_bots():
    while True:
        try:
            for pair in ['EUR/USD', 'XAU/USD']:
                signal = analyze_market(pair)
                if signal:
                    send_signal(pair, signal)
                else:
                    print(f"⏳ {pair}: لا توجد توصية حالياً...")
            send_hourly_status()
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
        time.sleep(60)
