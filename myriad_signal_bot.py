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
st.subheader("Strong Signals → Telegram Alert")
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

# ====================== IMPROVED DATA FETCH ======================
def get_binance_klines(symbol="BTCUSDT", interval="5m", limit=30):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        if not data or len(data) == 0:
            return None
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
        df['close'] = pd.to_numeric(df['close'])
        return df
    except:
        return None

def generate_signal(df, asset_name):
    if df is None or len(df) < 3:   # Lowered threshold for reliability
        return f"**WAITING** ({asset_name})", 0, "Not enough recent candles"
    
    current_price = float(df['close'].iloc[-1])
    # Use last 3 candles for momentum if we have less data
    lookback = min(5, len(df)-1)
    prev_price = float(df['close'].iloc[-lookback])
    
    if prev_price == 0:
        return f"**WAITING** ({asset_name})", 0, "Invalid price data"
    
    momentum = (current_price - prev_price) / prev_price * 100  # in percent for easier reading
    
    if momentum > 0.25:
        return f"**STRONG BUY — MORE GREEN** ({asset_name})", 85, f"Strong +{momentum:.2f}% momentum"
    elif momentum > 0.09:
        return f"**BUY — MORE GREEN** ({asset_name})", 68, f"Moderate +{momentum:.2f}% momentum"
    elif momentum < -0.25:
        return f"**STRONG BUY — MORE RED** ({asset_name})", 83, f"Strong {momentum:.2f}% momentum"
    elif momentum < -0.09:
        return f"**BUY — MORE RED** ({asset_name})", 70, f"Moderate {momentum:.2f}% momentum"
    else:
        return f"**NEUTRAL — WAIT** ({asset_name})", 50, f"Low momentum ({momentum:.2f}%)"

coins = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "ZEC": "ZECUSDT", "PENGU": "PENGUUSDT"}

# ====================== MAIN DASHBOARD ======================
if st.button("🔴 CHECK SIGNALS & SEND TELEGRAM (Strong Only)", type="primary", use_container_width=True):
    st.rerun()

st.subheader("Current Signals")
st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S UTC')}")

with st.spinner("Fetching latest data from Binance..."):
    alert_lines = [f"🔔 **Myriad 5-Min Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
    has_strong = False
    
    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df = get_binance_klines(symbol)
        
        if df is not None and len(df) >= 3:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            
            price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
            st.metric(f"Current {name} Price", price_str)
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason}")
            
            if conf >= 80:
                alert_lines.append(f"• **{signal}** | Confidence: {conf}% | Price: {price_str}")
                has_strong = True
                st.success("🔥 Strong signal detected!")
        else:
            st.warning(f"⏳ {name}: Still waiting for candle data (try refreshing)")
        
        st.markdown("---")

    # Auto-send Telegram if strong signal exists
    if has_strong:
        full_message = "\n".join(alert_lines)
        if send_telegram_alert(full_message):
            st.success("✅ Strong signal alert sent to Telegram!")
        else:
            st.warning("Could not send Telegram alert")
    else:
        st.info("No strong signals at the moment. Click the button again in a few minutes.")

st.warning("⚠️ High-risk prediction markets. These are momentum signals only. Trade responsibly.")

st.caption("Tip: Click the big button regularly or bookmark this page to receive alerts.")