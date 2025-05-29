import requests
import pandas as pd
import telebot
import datetime

# إعدادات TwelveData
API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
SYMBOLS = {'EUR/USD': 'EUR/USD', 'GOLD': 'XAU/USD'}
INTERVAL = '1min'
BASE_URL = 'https://api.twelvedata.com/time_series'

# إعدادات تيليجرام
TOKEN = '7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME'
CHAT_ID = '230315107'
bot = telebot.TeleBot(TOKEN)

def send_signal(signal):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    message = f"📊 توصية جديدة:

{signal}
🕐 الوقت: {now}
✅ نفّذ الآن يدويًا بفريم 1 دقيقة"
    bot.send_message(CHAT_ID, message)
    print(message)

def send_hourly_status():
    now = datetime.datetime.now().strftime('%H:%M:%S')
    bot.send_message(CHAT_ID, f"⏱️ البوت يعمل ✅ الساعة الآن: {now}")
    print(f"[{now}] إشعار الساعة")

def fetch_data(symbol):
    url = f"{BASE_URL}?symbol={symbol}&interval={INTERVAL}&outputsize=100&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if 'values' not in data:
        print(f"❌ فشل في جلب بيانات {symbol}")
        return None
    df = pd.DataFrame(data['values'])
    df['close'] = df['close'].astype(float)
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df.sort_values('datetime')

def calculate_indicators(df):
    df['delta'] = df['close'].diff()
    df['gain'] = df['delta'].where(df['delta'] > 0, 0).rolling(window=14).mean()
    df['loss'] = -df['delta'].where(df['delta'] < 0, 0).rolling(window=14).mean()
    rs = df['gain'] / df['loss']
    df['rsi'] = 100 - (100 / (1 + rs))
    df['sma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper_band'] = df['sma'] + 2 * df['std']
    df['lower_band'] = df['sma'] - 2 * df['std']
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    return df

def analyze_market():
    messages = []
    for label, symbol in SYMBOLS.items():
        df = fetch_data(symbol)
        if df is None:
            continue
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        rsi = latest['rsi']
        close = latest['close']
        macd = latest['macd']
        signal_line = latest['macd_signal']
        upper = latest['upper_band']
        lower = latest['lower_band']

        buy = rsi < 30 and close < lower and macd > signal_line
        sell = rsi > 70 and close > upper and macd < signal_line

        if buy:
            messages.append(f"💹 {label}: إشــارة *شراء*")
        elif sell:
            messages.append(f"📉 {label}: إشــارة *بيع*")
    return "\n\n".join(messages) if messages else None