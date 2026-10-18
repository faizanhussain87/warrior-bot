from flask import Flask
import os
import threading
import time

app = Flask(__name__)

def trading_loop():
while True:
print("Ross Bot FREE Running")
time.sleep(60)

@app.route('/')
def home():
return "Ross Bot FREE is LIVE"

@app.route('/health')
def health():
return "OK"

if __name__ == '__main__':
t = threading.Thread(target=trading_loop, daemon=True)
t.start()
port = int(os.environ.get("PORT", 10000))
app.run(host='0.0.0.0', port=port)
