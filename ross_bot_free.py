code="""
from flask import Flask
import os, threading, time
app=Flask(__name__)
def trading_loop():
    while True:
        print("Ross Bot FREE Running")
        time.sleep(60)
@app.route('/')
def home():
    return "Ross Bot FREE is LIVE - Deployed!"
@app.route('/health')
def health():
    return "OK"
if __name__=='__main__':
    import threading as th
    t=th.Thread(target=trading_loop, daemon=True)
    t.start()
    port=int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0', port=port)
"""
exec(code)
