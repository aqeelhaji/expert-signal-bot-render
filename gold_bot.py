
import requests
import time
import datetime
import telebot
import pandas as pd

TOKEN = "7901371888:AAFxzcndqyccegYv9uVWAm4UnP1guO5AeME"
CHAT_ID = "230315107"
bot = telebot.TeleBot(TOKEN)

API_KEY = 'dd98455cbb9b4161b38d5d8e561b5f72'
SYMBOL = 'XAU/USD'
INTERVAL = '1min'
API_URL = f'https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval={INTERVAL}&outputsize=100&apikey={API_KEY}'

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

def analyze_market():
    response = requests.get(API_URL)
    data = response.json()
    if 'values' not in data:
        print("❌ فشل في جلب بيانات الذهب")
        return None
    df = pd.DataFrame(data['values'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    buy = latest['rsi'] < 30 and latest['close'] < latest['lower_band'] and latest['macd'] > latest['macd_signal']
    sell = latest['rsi'] > 70 and latest['close'] > latest['upper_band'] and latest['macd'] < latest['macd_signal']
    if buy:
        return "شراء الذهب 🟢"
    elif sell:
        return "بيع الذهب 🔴"
    else:
        return None

def send_signal(signal):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    message = f"📈 توصية GOLD: {signal}
🕐 الوقت: {now}
⏱️ الفريم: 1:30 دقيقة"
    print(message)
    bot.send_message(CHAT_ID, message)

def run_gold():
    while True:
        try:
            signal = analyze_market()
            if signal:
                send_signal(signal)
            else:
                print("⏳ GOLD: لا توجد توصية حالياً...")
        except Exception as e:
            print(f"⚠️ خطأ GOLD: {e}")
        time.sleep(60)
