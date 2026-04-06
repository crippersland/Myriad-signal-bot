import streamlit as st
import requests
import pandas as pd
import time
import threading
from datetime import datetime

# ====================== YOUR CREDENTIALS (Hardcoded) ======================
# ====================== TELEGRAM CREDENTIALS ======================
# For local run: hardcoded (you can keep for now)
# For deployed version: we will use st.secrets below

try:
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
except:
    # Fallback for local testing
    TELEGRAM_TOKEN = "8367700487:AAEGh_e1zSdxZGFW7eG7tSCaWhAcI79dnVg"
    TELEGRAM_CHAT_ID = "6081249024"

# ====================== DARK MODE SETUP ======================
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

# ====================== DATA & SIGNAL LOGIC ======================
def get_binance_klines(symbol="BTCUSDT", interval="5m", limit=30):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
        df['close'] = pd.to_numeric(df['close'])
        return df
    except:
        return None

def generate_signal(df, asset_name):
    if df is None or len(df) < 5:
        return f"**ERROR** ({asset_name})", 0, "Data fetch failed"
    
    current_price = float(df['close'].iloc[-1])
    momentum = (current_price - float(df['close'].iloc[-5])) / float(df['close'].iloc[-5])
    
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

coins = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "ZEC": "ZECUSDT", "PENGU": "PENGUUSDT"}

# ====================== BACKGROUND AUTO ALERT (STRONG SIGNALS ONLY) ======================
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
                    
                    if conf >= 80:   # Only strong signals
                        alert_lines.append(f"• **{signal}** | Confidence: {conf}% | Price: ${price:,.4f if name == 'PENGU' else ',.0f'}")
                        has_strong = True
            
            if has_strong:
                full_message = "\n".join(alert_lines)
                send_telegram_alert(full_message)
                if "last_alert" not in st.session_state:
                    st.session_state.last_alert = datetime.now()
                else:
                    st.session_state.last_alert = datetime.now()
                    
        except:
            pass
        
        time.sleep(300)  # Every 5 minutes

# Start the background thread
if "background_thread_started" not in st.session_state:
    thread = threading.Thread(target=background_alert_sender, daemon=True)
    thread.start()
    st.session_state.background_thread_started = True
    st.success("✅ Auto-alert system started! Strong signals will be sent to your Telegram every 5 minutes.")

# ====================== LIVE DASHBOARD ======================
if st.button("🔴 Manual Refresh Signals Now", type="primary", use_container_width=True):
    st.rerun()

st.subheader("Live Signals")

with st.spinner("Fetching latest candle data..."):
    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df = get_binance_klines(symbol)
        if df is not None:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            
            st.metric(f"Current {name} Price", f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}")
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason}")
            
            if conf >= 80:
                st.success("🔥 Strong signal detected!")
            
            st.info("→ Open Myriad Markets → 5-Min Candles and take the matching position")
        else:
            st.error(f"Could not load {name} data")
        st.markdown("---")

if "last_alert" in st.session_state:
    st.caption(f"🕒 Last strong alert sent: {st.session_state.last_alert.strftime('%H:%M:%S UTC')}")

st.warning("⚠️ High risk. These are momentum-based signals only. Trade responsibly.")

st.caption("Your bot is running with your credentials. Keep this window open.")