import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ====================== YOUR CREDENTIALS ======================
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    TELEGRAM_TOKEN = "8367700487:AAEGh_e1zSdxZGFW7eG7tSCaWhAcI79dnVg"
    TELEGRAM_CHAT_ID = "6081249024"

# ====================== DARK MODE ======================
st.set_page_config(page_title="Myriad 5-Min Bot", page_icon="🚀", layout="wide")

with st.sidebar:
    dark_mode = st.toggle("🌙 Dark Mode", value=True)
    if dark_mode:
        st.markdown("""
        <style>
            .stApp { background-color: #0E1117; color: #FAFAFA; }
            .stMetric { background-color: #1E1F26; }
        </style>
        """, unsafe_allow_html=True)

st.title("🚀 Myriad Markets 5-Min Candle Signal Bot")
st.subheader("Confidence for All • Alerts Only ≥80%")
st.caption("BTC • ETH • BNB • ZEC • PENGU | Multiple Data Sources")

def send_telegram_alert(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        return True
    except:
        st.error("Telegram send failed")
        return False

# ====================== MULTI-SOURCE CANDLE FETCH ======================
def get_klines(symbol):
    # 1. Binance Futures (most reliable for 5m)
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=20"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            if len(data) >= 2:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "Binance Futures"
    except:
        pass

    # 2. Binance Spot fallback
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=20"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            if len(data) >= 2:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "Binance Spot"
    except:
        pass

    # 3. CoinGecko fallback (for PENGU and others)
    try:
        coin_id = {"BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "BNBUSDT": "binancecoin", 
                   "ZECUSDT": "zcash", "PENGUUSDT": "pudgy-penguins"}.get(symbol, "bitcoin")
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1&interval=5m"
        r = requests.get(url, timeout=10)
        if r.ok:
            data = r.json()
            prices = data.get("prices", [])
            if len(prices) >= 3:
                df = pd.DataFrame(prices, columns=['time', 'close'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "CoinGecko"
    except:
        pass

    return None, "Failed"

def generate_signal(df, asset_name):
    if df is None or len(df) < 2:
        return f"**WAITING** ({asset_name})", 0, "No data"
    
    current_price = float(df['close'].iloc[-1])
    lookback = min(5, len(df)-1)
    prev_price = float(df['close'].iloc[-lookback])
    
    if prev_price == 0:
        return f"**WAITING** ({asset_name})", 0, "Invalid price"
    
    momentum = (current_price - prev_price) / prev_price * 100
    
    if momentum > 0.25:
        return f"**STRONG BUY — MORE GREEN** ({asset_name})", 85, f"Strong +{momentum:.2f}%"
    elif momentum > 0.09:
        return f"**BUY — MORE GREEN** ({asset_name})", 68, f"Moderate +{momentum:.2f}%"
    elif momentum < -0.25:
        return f"**STRONG BUY — MORE RED** ({asset_name})", 83, f"Strong {momentum:.2f}%"
    elif momentum < -0.09:
        return f"**BUY — MORE RED** ({asset_name})", 70, f"Moderate {momentum:.2f}%"
    else:
        return f"**NEUTRAL — WAIT** ({asset_name})", 50, f"Low momentum ({momentum:.2f}%)"

coins = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "ZEC": "ZECUSDT", "PENGU": "PENGUUSDT"}

# ====================== DASHBOARD ======================
if st.button("🔴 CHECK SIGNALS & SEND TELEGRAM (Only ≥80%)", type="primary", use_container_width=True):
    st.rerun()

st.subheader("Current Signals")
st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S UTC')}")

with st.spinner("Trying Binance Futures → Spot → CoinGecko..."):
    alert_lines = [f"🔔 **Myriad 5-Min Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
    has_strong = False
    
    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df, source = get_klines(symbol)
        
        if df is not None and len(df) >= 2:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            
            price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
            
            st.metric(f"Current {name} Price", price_str)
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason} | Source: {source}")
            
            if conf >= 80:
                st.success("🔥 STRONG SIGNAL — Recommended to Buy on Myriad!")
                alert_lines.append(f"• **{signal}** | Confidence: {conf}% | Price: {price_str}")
                has_strong = True
        else:
            st.error(f"❌ {name}: No data from any source")
        
        st.markdown("---")

    if has_strong:
        full_message = "\n".join(alert_lines)
        if send_telegram_alert(full_message):
            st.success("✅ Strong signal alert sent to Telegram!")
    else:
        st.info("No strong signals (≥80%) right now.")

st.warning("⚠️ Only trade when confidence ≥ 80%. High risk — use responsibly.")

st.caption("Now using 3 data sources for better reliability.")