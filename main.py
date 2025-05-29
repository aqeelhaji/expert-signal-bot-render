import time
import threading
from keep_alive import keep_alive
from signal_logic import analyze_market, send_signal, send_hourly_status

keep_alive()

def run_bot():
    last_status_time = time.time()
    while True:
        try:
            signal = analyze_market()
            if signal:
                send_signal(signal)
            # إشعار كل ساعة أن البوت يعمل
            if time.time() - last_status_time >= 3600:
                send_hourly_status()
                last_status_time = time.time()
            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(60)

threading.Thread(target=run_bot).start()