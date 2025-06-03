import requests
import pandas as pd
import telebot
import datetime
import time

# إعدادات البوتات
GOLD_TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
EUR_TOKEN = '8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE'
GOLD_CHAT_ID = '230315107'
EUR_CHAT_ID = '230315107'

# إعدادات TwelveData
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
URLS = {
    'XAU/USD': f'https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1min&apikey={API_KEY}&outputsize=100',
    'EUR/USD': f'https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=30s&apikey={API_KEY}&outputsize=100'
}

bots = {
    'XAU/USD': telebot.TeleBot(GOLD_TOKEN),
    'EUR/USD': telebot.TeleBot(EUR_TOKEN)
}

def send_signal(pair, signal, chat_id):
    message = f"""📊 توصية مؤكدة لـ {pair}:
✅ {signal}
⏱️ نفّذ الصفقة بفريم 1:30 دقيقة"""
    bots[pair].send_message(chat_id, message)

def send_possible(pair, signal, points_diff, chat_id):
    message = f"""⚠️ توصية محتملة لـ {pair}:
🔄 الاتجاه: {signal}
📍المتبقي لتحقيق الشرط الثالث: {points_diff:.4f} نقطة"
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
        url = URLS[pair]
        response = requests.get(url)
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

        if rsi < 30 and close < lower_band and macd > macd_signal:
            send_signal(pair, "شراء", chat_id)
        elif rsi > 70 and close > upper_band and macd < macd_signal:
            send_signal(pair, "بيع", chat_id)
        else:
            if rsi < 30 and macd > macd_signal:
                diff = abs(close - lower_band)
                if diff <= 0.0010:
                    send_possible(pair, "شراء", diff, chat_id)
            elif rsi > 70 and macd < macd_signal:
                diff = abs(close - upper_band)
                if diff <= 0.0010:
                    send_possible(pair, "بيع", diff, chat_id)
    except Exception as e:
        print(f"خطأ {pair}: {e}")

def run_bots():
    last_status = {'XAU/USD': 0, 'EUR/USD': 0}
    while True:
        now = time.time()
        for pair in ['XAU/USD', 'EUR/USD']:
            chat_id = GOLD_CHAT_ID if pair == 'XAU/USD' else EUR_CHAT_ID
            analyze(pair, chat_id)
            if now - last_status[pair] > 3600:
                send_hourly_status(pair, chat_id)
                last_status[pair] = now
        time.sleep(60)
