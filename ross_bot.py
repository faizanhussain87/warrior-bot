import os, time, requests, threading
from datetime import datetime
import pytz
from flask import Flask
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame

# --- KEYS FROM RENDER ENVIRONMENT VARIABLES ---
ALPACA_KEY = os.environ.get("ALPACA_KEY")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CHICAGO = pytz.timezone("America/Chicago")
app = Flask(__name__)

# Initialize clients
trading = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)

def send_tg(msg):
try:
requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
except: pass

def get_top_gappers():
tickers = ["BDRX","NLSP","SPRC","GNS","HOLO","FFIE","SINT","PRST","TIVC","LUCY","AIMD","CDIO"]
gappers = []
for sym in tickers:
try:
snap_req = StockSnapshotRequest(symbol_or_symbols=sym)
snap = data_client.get_stock_snapshot(snap_req)[sym]
prev_close = snap.previous_daily_bar.close if snap.previous_daily_bar else snap.daily_bar.close
curr_price = snap.latest_trade.price
if prev_close == 0: continue
gap = (curr_price / prev_close - 1) * 100
if 2 <= curr_price <= 20 and gap >= 10:
gappers.append({"symbol": sym, "price": curr_price, "gap": gap})
except: continue
return sorted(gappers, key=lambda x: x["gap"], reverse=True)[:5]

def check_bull_flag(symbol):
try:
req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, limit=50)
bars = data_client.get_stock_bars(req).data.get(symbol, [])
if len(bars) < 20: return None
closes = [b.close for b in bars]
highs = [b.high for b in bars]
lows = [b.low for b in bars]
consolidation_high = max(highs[-10:-3])
consolidation_low = min(lows[-10:-3])
range_pct = (consolidation_high - consolidation_low) / consolidation_low * 100
current_price = closes[-1]
volume_spike = bars[-1].volume > bars[-2].volume * 1.2
if range_pct < 3.0 and current_price > consolidation_high and volume_spike:
return {"entry": current_price, "stop": consolidation_low - 0.05}
return None
except: return None

def run_ross_bot():
send_tg(f"🚀 FREE ROSS BOT LIVE - {datetime.now(CHICAGO).strftime('%I:%M %p Chicago')}")
traded_today = set()
while True:
try:
now = datetime.now(CHICAGO)
if now.weekday() >= 5:
time.sleep(60); continue
market_open = now.replace(hour=8, minute=30, second=0)
market_close = now.replace(hour=10, minute=0, second=0)

if not (market_open <= now <= market_close):
if now.hour == 8 and now.minute % 10 == 0:
gappers = get_top_gappers()
if gappers:
msg = f"🔍 PRE-MARKET {now.strftime('%I:%M %p')}:\n"
for g in gappers:
msg += f"{g['symbol']}: ${g['price']:.2f} +{g['gap']:.1f}%\n"
send_tg(msg)
time.sleep(60); continue

gappers = get_top_gappers()
for stock in gappers:
sym = stock['symbol']
if sym in traded_today: continue
setup = check_bull_flag(sym)
if setup:
entry = setup['entry']
stop = setup['stop']
if entry - stop <= 0 or entry - stop > 1.0: continue
order = MarketOrderRequest(symbol=sym, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
trading.submit_order(order)
traded_today.add(sym)
send_tg(f"✅ BUY {sym} @ ${entry:.2f} Gap +{stock['gap']:.1f}% Stop ${stop:.2f}")
stop_order = StopOrderRequest(symbol=sym, qty=1, side=OrderSide.SELL, stop_price=stop, time_in_force=TimeInForce.DAY)
trading.submit_order(stop_order)
time.sleep(30)
except Exception as e:
time.sleep(30)

# Fake web server to keep Render Free alive
@app.route('/')
def home():
return "Ross Bot is Running - Free Tier - Chicago"

@app.route('/ping')
def ping():
return "pong"

# Start bot in background thread
threading.Thread(target=run_ross_bot, daemon=True).start()

if __name__ == "__main__":
app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
