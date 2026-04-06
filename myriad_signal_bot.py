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
st.subheader("Confidence Shown for All • Alerts Only ≥80%")
st.caption("BTC • ETH • BNB • ZEC • PENGU | Built for TheCryptomajor")

def send_telegram_alert(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        return True
    except:
        st.error("Failed to send Telegram alert")
        return False

# ====================== DUAL SOURCE DATA FETCH (Stable Version) ======================
def get_klines(symbol):
    # Try Futures first
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=30"
        r = requests.get(url, timeout=12)
        if r.ok:
            data = r.json()
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "Futures"
    except:
        pass

    # Fallback to Spot
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=30"
        r = requests.get(url, timeout=12)
        if r.ok:
            data = r.json()
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "Spot"
    except:
        pass

    return None, "No data"

def generate_signal(df, asset_name):
    if df is None or len(df) < 3:
        return f"**WAITING** ({asset_name})", 0, "Not enough candles"
    
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

coins = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "ZEC": "ZECUSDT",
    "PENGU": "PENGUUSDT"
}

# ====================== MAIN DASHBOARD ======================
if st.button("🔴 CHECK SIGNALS & SEND TELEGRAM (Only ≥80%)", type="primary", use_container_width=True):
    st.rerun()

st.subheader("Current Signals")
st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S UTC')}")

with st.spinner("Fetching 5-min candle data..."):
    alert_lines = [f"🔔 **Myriad 5-Min Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
    has_strong = False
    
    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df, source = get_klines(symbol)
        
        if df is not None and len(df) >= 3:
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
            st.warning(f"⏳ {name}: Waiting for candle data (Source: {source})")
        
        st.markdown("---")

    if has_strong:
        full_message = "\n".join(alert_lines)
        if send_telegram_alert(full_message):
            st.success("✅ Strong signal alert sent to Telegram!")
    else:
        st.info("No strong signals (≥80% confidence) at the moment.")

st.warning("⚠️ High-risk. Only take positions when confidence ≥ 80%. Trade responsibly.")

st.caption("Reverted to previous stable version. Click the button to refresh.")