import streamlit as st
import requests
import pandas as pd
import time
import threading
from datetime import datetime

# ====================== TELEGRAM CREDENTIALS ======================
try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    # Fallback for safety (you already set secrets on Streamlit)
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
st.subheader("Auto Telegram Alerts (Strong Signals Only)")
st.caption("BTC • ETH • BNB • ZEC • PENGU | Built for TheCryptomajor")

def send_telegram_alert(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        return True
    except:
        return False

# ====================== DATA FETCH WITH SAFETY ======================
def get_binance_klines(symbol="BTCUSDT", interval="5m", limit=30):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
        df['close'] = pd.to_numeric(df['close'])
        return df
    except:
        return None

def generate_signal(df, asset_name):
    if df is None or len(df) < 6:   # Need at least 6 rows for safety
        return f"**WAITING** ({asset_name})", 0, "Not enough candle data yet"
    
    current_price = float(df['close'].iloc[-1])
    prev_price = float(df['close'].iloc[-5])
    
    if prev_price == 0:
        return f"**WAITING** ({asset_name})", 0, "Price data issue"
    
    momentum = (current_price - prev_price) / prev_price
    
    if momentum > 0.0025:
        return f"**STRONG BUY — MORE GREEN** ({asset_name})", 85, "Strong bullish momentum"
    elif momentum > 0.0009:
        return f"**BUY — MORE GREEN** ({asset_name})", 68, "Moderate upward bias"
    elif momentum < -0.0025:
        return f"**STRONG BUY — MORE RED** ({asset_name})", 83, "Strong bearish momentum"
    elif momentum < -0.0009:
        return f"**BUY — MORE RED** ({asset_name})", 70, "Moderate downward bias"
    else:
        return f"**NEUTRAL — WAIT** ({asset_name})", 50, "Choppy market"

coins = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "ZEC": "ZECUSDT",
    "PENGU": "PENGUUSDT"
}

# ====================== BACKGROUND AUTO ALERT (STRONG ONLY) ======================
def background_alert_sender():
    while True:
        try:
            alert_lines = [f"🔔 **Myriad 5-Min Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
            has_strong = False
            
            for name, symbol in coins.items():
                df = get_binance_klines(symbol)
                if df is not None:
                    price = float(df['close'].iloc[-1])
                    signal, conf, reason = generate_signal(df, name)
                    
                    if conf >= 80:
                        price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
                        alert_lines.append(f"• **{signal}** | Confidence: {conf}% | Price: {price_str}")
                        has_strong = True
            
            if has_strong:
                full_message = "\n".join(alert_lines)
                send_telegram_alert(full_message)
                st.session_state.last_alert = datetime.now()
                
        except:
            pass
        
        time.sleep(300)  # 5 minutes

# Start background thread
if "background_thread_started" not in st.session_state:
    thread = threading.Thread(target=background_alert_sender, daemon=True)
    thread.start()
    st.session_state.background_thread_started = True
    st.success("✅ Auto-alert system running! Strong signals (≥80%) will be sent to Telegram every 5 minutes.")

# ====================== LIVE DASHBOARD ======================
if st.button("🔴 Manual Refresh Signals Now", type="primary", use_container_width=True):
    st.rerun()

st.subheader("Live Signals Dashboard")

with st.spinner("Fetching latest 5-min candle data..."):
    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df = get_binance_klines(symbol)
        
        if df is not None and len(df) >= 6:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            
            price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
            st.metric(f"Current {name} Price", price_str)
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason}")
            
            if conf >= 80:
                st.success("🔥 Strong signal detected!")
            
            st.info("→ Go to Myriad Markets → 5-Min Candles and match **More Green** or **More Red**")
        else:
            st.warning(f"⏳ {name}: Waiting for more candle data...")
        
        st.markdown("---")

if "last_alert" in st.session_state:
    st.caption(f"🕒 Last strong alert sent: {st.session_state.last_alert.strftime('%H:%M:%S UTC')}")

st.warning("⚠️ High-risk prediction markets. Momentum-based signals only. Trade responsibly.")

st.caption("Bot deployed on Streamlit Cloud • Dark mode enabled • Strong signals only")