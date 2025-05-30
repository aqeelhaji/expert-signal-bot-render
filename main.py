
from flask import Flask
import threading
from signal_logic import run_bots

app = Flask(__name__)

@app.route('/')
def home():
    return "📡 Expert Signal Bot is Running."

if __name__ == "__main__":
    threading.Thread(target=run_bots).start()
    app.run(host='0.0.0.0', port=8080)
