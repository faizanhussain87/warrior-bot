from flask import Flask
import os
import time
import threading
from datetime import datetime
import pytz
import requests

app = Flask(__name__)

# Environment variables from Render
ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
try:
if TELEGRAM_TOKEN and CHAT_ID:
url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
except Exception as e:
print(f"Telegram error: {e}")

def trading_loop():
while True:
try:
now = datetime.now(pytz.timezone('US/Eastern'))
print(f"[{now}] Ross Bot Running - Checking Market...")
# Your trading logic here
time.sleep(60)
except Exception as e:
print(f"Loop error: {e}")
time.sleep(60)

@app.route('/')
def home():
return "Ross Bot is Running - FREE Version"

@app.route('/health')
def health():
return "OK", 200

if __name__ == '__main__':
print("Starting Ross Bot FREE...")
send_telegram("✅ Ross Bot FREE Deployed Successfully!")
# Start trading in background thread
t = threading.Thread(target=trading_loop, daemon=True)
t.start()
# Start Flask for Render health checks
port = int(os.environ.get("PORT", 10000))
app.run(host='0.0.0.0', port=port)
