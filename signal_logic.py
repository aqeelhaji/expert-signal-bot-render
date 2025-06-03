
import requests
import pandas as pd
import telebot
import datetime
import time

# إعدادات توكنات تيليجرام والدردشة
GOLD_TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
EUR_TOKEN = '8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE'
CHAT_ID = '230315107'

bots = {
    'XAU/USD': telebot.TeleBot(GOLD_TOKEN),
    'EUR/USD': telebot.TeleBot(EUR_TOKEN)
}

# إعدادات TwelveData API
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
URLS = {
    'XAU/USD': f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100',
    'EUR/USD': f'https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=30s&apikey={API_KEY}&outputsize=100'
}

def send_signal(pair, signal, chat_id, conditions):
    message = f"📊 توصية جديدة لـ {pair}:
✅ {signal}
📉 تحقق {conditions} من 3 شروط
⏱️ نفّذ الصفقة بفريم {'1:30' if pair == 'XAU/USD' else '0:30'} دقيقة"
    bots[pair].send_message(chat_id, message)

def send_possible(pair, diff, chat_id):
    message = f"⚠️ توصية محتملة لـ {pair}
📍المتبقي لتحقيق الشرط: {diff:.5f} نقطة"
    bots[pair].send_message(chat_id, message)

def send_hourly_status(pair, chat_id):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    bots[pair].send_message(chat_id, f"⏱️ البوت ({pair}) يعمل ✅ الساعة الآن: {now}")

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

def analyze(pair, chat_id):
    try:
        response = requests.get(URLS[pair])
        data = response.json()
        if 'values' not in data:
            return
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df = calculate_indicators(df)
        latest = df.iloc[-1]

        close = latest['close']
        rsi = latest['rsi']
        macd = latest['macd']
        macd_signal = latest['macd_signal']
        lower_band = latest['lower_band']
        upper_band = latest['upper_band']

        conditions = 0
        if rsi < 30 or rsi > 70:
            conditions += 1
        if (rsi < 30 and close < lower_band) or (rsi > 70 and close > upper_band):
            conditions += 1
        if (rsi < 30 and macd > macd_signal) or (rsi > 70 and macd < macd_signal):
            conditions += 1

        if conditions >= 2:
            direction = "شراء" if rsi < 30 else "بيع"
            send_signal(pair, direction, chat_id, conditions)
        elif conditions == 1:
            diff = abs(close - (lower_band if rsi < 30 else upper_band))
            if diff <= 0.0010:
                send_possible(pair, diff, chat_id)

    except Exception as e:
        print(f"خطأ في {pair}: {e}")

def run_bots():
    last_status = {'XAU/USD': 0, 'EUR/USD': 0}
    while True:
        now = time.time()
        for pair in ['XAU/USD', 'EUR/USD']:
            analyze(pair, CHAT_ID)
            if now - last_status[pair] >= 3600:
                send_hourly_status(pair, CHAT_ID)
                last_status[pair] = now
        time.sleep(60)
