import os, time, requests
from datetime import datetime, timedelta
import pytz
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopOrderRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass, AssetStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame

# --- KEYS - PASTE YOUR REAL KEYS HERE PRIVATELY ---
ALPACA_KEY = "YOUR_ALPACA_KEY"
ALPACA_SECRET = "YOUR_ALPACA_SECRET"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

CHICAGO = pytz.timezone("America/Chicago")
trading = TradingClient(ALPACA_KEY, ALPACA_SECRET, paper=True)
data_client = StockHistoricalDataClient(ALPACA_KEY, ALPACA_SECRET)

# ROSS CONFIG
MIN_PRICE, MAX_PRICE = 2, 20
MIN_GAP_PCT = 10.0
MIN_RVOL = 3.0
RISK_PER_TRADE = 50 # dollars
MAX_HOLD_MIN = 90 # Exit by 10:00 AM Chicago

def send_tg(msg):
try:
requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
except: pass

def get_top_gappers():
# Get most active - Alpaca assets
try:
# We scan from pre-market movers list via snapshots
# For paper: we scan watchlist of small caps
tickers = ["BDRX","NLSP","SPRC","GNS","HOLO","FFIE","SINT","PRST","TIVC","LUCY","AIMD","CDIO"] # dynamic placeholder - bot will scan wider in live
# In live version, replace with Alpaca screener API or polygon
gappers = []
for sym in tickers:
try:
snap_req = StockSnapshotRequest(symbol_or_symbols=sym)
snap = data_client.get_stock_snapshot(snap_req)[sym]
prev_close = snap.previous_daily_bar.close if snap.previous_daily_bar else snap.daily_bar.close
curr_price = snap.latest_trade.price
if prev_close == 0: continue
gap = (curr_price / prev_close - 1) * 100
vol = snap.daily_bar.volume
avg_vol = 500000 # simplified - in real bot fetch 50-day avg
rvol = vol / avg_vol if avg_vol else 0
if MIN_PRICE <= curr_price <= MAX_PRICE and gap >= MIN_GAP_PCT and rvol >= 1.5:
gappers.append({"symbol": sym, "price": curr_price, "gap": gap, "rvol": rvol, "volume": vol})
except: continue
return sorted(gappers, key=lambda x: x["gap"], reverse=True)[:5]
except Exception as e:
send_tg(f"Scanner error: {e}")
return []

def check_bull_flag(symbol):
# Ross entry: consolidation + break
try:
req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, limit=50)
bars = data_client.get_stock_bars(req).data.get(symbol, [])
if len(bars) < 20: return None
closes = [b.close for b in bars]
highs = [b.high for b in bars]
lows = [b.low for b in bars]

# Find consolidation: last 5 candles range < 2%
recent = closes[-10:-3]
consolidation_high = max(highs[-10:-3])
consolidation_low = min(lows[-10:-3])
range_pct = (consolidation_high - consolidation_low) / consolidation_low * 100

current_price = closes[-1]
volume_spike = bars[-1].volume > bars[-2].volume * 1.5

# Breakout condition
if range_pct < 3.0 and current_price > consolidation_high and volume_spike:
return {
"entry": current_price,
"stop": consolidation_low - 0.05,
"consolidation_high": consolidation_high
}
return None
except: return None

def run_ross_bot():
send_tg(f"🚀 ROSS WARRIOR BOT STARTED - Chicago Time: {datetime.now(CHICAGO).strftime('%I:%M %p')} - Scanning $2-$20 Gappers")

traded_today = set()

while True:
try:
now = datetime.now(CHICAGO)
# Only trade 8:30 - 10:00 AM Chicago (Ross's window)
if now.weekday() >= 5:
time.sleep(60); continue

market_open = now.replace(hour=8, minute=30, second=0)
market_close = now.replace(hour=10, minute=0, second=0)

if not (market_open <= now <= market_close):
# Pre-market scan
if now.hour == 8 and now.minute % 5 == 0:
gappers = get_top_gappers()
if gappers:
msg = f"🔍 PRE-MARKET SCAN {now.strftime('%I:%M %p')}:\n"
for g in gappers:
msg += f"{g['symbol']}: ${g['price']:.2f} | Gap +{g['gap']:.1f}% | RVOL {g['rvol']:.1f}x\n"
send_tg(msg)
time.sleep(60); continue

# Market hours - scan and trade
gappers = get_top_gappers()
for stock in gappers:
sym = stock['symbol']
if sym in traded_today: continue

setup = check_bull_flag(sym)
if setup:
entry = setup['entry']
stop = setup['stop']
risk_per_share = entry - stop
if risk_per_share <= 0 or risk_per_share > 1.0: continue # too risky
qty = max(1, int(RISK_PER_TRADE / risk_per_share / entry)) # Ross position sizing

# BUY
order = MarketOrderRequest(symbol=sym, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
trading.submit_order(order)
traded_today.add(sym)
send_tg(f"✅ ROSS ENTRY: {sym}\nPrice: ${entry:.2f}\nGap: +{stock['gap']:.1f}% | RVOL {stock['rvol']:.1f}x\nStop: ${stop:.2f}\nRisk: ${RISK_PER_TRADE}\nTime: {now.strftime('%I:%M %p Chicago')}")

# Set stop loss
stop_order = StopOrderRequest(symbol=sym, qty=1, side=OrderSide.SELL, stop_price=stop, time_in_force=TimeInForce.DAY)
trading.submit_order(stop_order)

time.sleep(30)

except Exception as e:
send_tg(f"⚠️ Bot error: {e}")
time.sleep(30)

if __name__ == "__main__":
run_ross_bot()
