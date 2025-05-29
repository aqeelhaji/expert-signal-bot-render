
import requests
import datetime
import time
import telebot
import pandas as pd
from keep_alive import keep_alive
from threading import Thread
import platform

TOKEN = "8148594075:AAGKcG9S6qC69ARIRCVUS3aN4CfdBDAd4xE"
CHAT_ID = "230315107"
bot = telebot.TeleBot(TOKEN)

API_KEY = "dd98455cbb9b4161b38d5d8e561b5f72"
API_URL = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&outputsize=50&apikey={API_KEY}"

def fetch_data():
    try:
        response = requests.get(API_URL)
        data = response.json()
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime")
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print("⚠️ EUR/USD - خطأ في جلب البيانات:", e)
        return None

def calculate_indicators(df):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    rsi = latest["RSI"]
    macd = latest["MACD"]
    signal_line = latest["Signal"]
    if rsi < 30 and macd > signal_line:
        return "BUY 📈 (EUR/USD)"
    elif rsi > 70 and macd < signal_line:
        return "SELL 📉 (EUR/USD)"
    else:
        return None

def send_signal(rec):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    msg = f"""
📊 توصية EUR/USD

📈 التوصية: {rec}
🕐 الوقت: {now}
⏱️ الفريم: 1 دقيقة
"""
    print(msg)
    bot.send_message(CHAT_ID, msg)

def run_eurusd():
    keep_alive()
    while True:
        df = fetch_data()
        if df is not None:
            df = calculate_indicators(df)
            rec = generate_signal(df)
            if rec:
                send_signal(rec)
            else:
                print(f"⏳ EUR/USD: لا توجد توصية حالياً...")
        time.sleep(30)
