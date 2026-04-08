import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# ====================== CONFIG ======================
TELEGRAM_TOKEN = "8367700487:AAEGh_e1zSdxZGFW7eG7tSCaWhAcI79dnVg"
USERS_FILE = "telegram_users.txt"

# Load and save users
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip().isdigit()]
    return []

def save_user(chat_id):
    users = load_users()
    if chat_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")
        return True
    return False

def send_to_all_users(message: str):
    users = load_users()
    sent = 0
    for chat_id in users:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            if requests.post(url, data=data, timeout=10).ok:
                sent += 1
        except:
            pass
    return sent, len(users)

# ====================== DARK MODE ======================
st.set_page_config(page_title="Myriad 5-Min Bot", page_icon="🚀", layout="wide")

with st.sidebar:
    dark_mode = st.toggle("🌙 Dark Mode", value=True)
    if dark_mode:
        st.markdown("<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>", unsafe_allow_html=True)

st.title("🚀 Myriad Markets 5-Min Public Signal Bot")
st.subheader("Anyone can join • Strong signals broadcast to all")
st.caption("Built for TheCryptomajor")

# ====================== DATA FETCH ======================
def get_klines(symbol):
    try:
        # Try Futures
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=20"
        r = requests.get(url, timeout=12)
        if r.ok:
            data = r.json()
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "Futures"
    except:
        pass

    try:
        # Try Spot
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=20"
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
        return f"**WAITING** ({asset_name})", 0, "Not enough candles yet"
    
    current = float(df['close'].iloc[-1])
    prev = float(df['close'].iloc[-3])
    momentum = (current - prev) / prev * 100 if prev != 0 else 0
    
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

# ====================== MAIN DASHBOARD ======================
if st.button("🔴 REFRESH SIGNALS & BROADCAST STRONG ONES", type="primary", use_container_width=True):
    st.rerun()

st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S UTC')} | Subscribers: {len(load_users())}")

with st.spinner("Fetching latest 5-min candles..."):
    alert_lines = [f"🔔 **Myriad 5-Min Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
    has_strong = False

    for name, symbol in coins.items():
        st.subheader(f"{name}")
        df, source = get_klines(symbol)
        
        if df is not None and len(df) >= 3:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
            
            st.metric(f"Current Price", price_str)
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason} | Source: {source}")
            
            if conf >= 80:
                st.success("🔥 STRONG SIGNAL — Recommended to Buy on Myriad!")
                alert_lines.append(f"• **{signal}** | Confidence: {conf}% | Price: {price_str}")
                has_strong = True
        else:
            st.warning(f"⏳ {name}: Waiting for candle data...")
        
        st.markdown("---")

    if has_strong:
        full_message = "\n".join(alert_lines)
        sent, total = send_to_all_users(full_message)
        st.success(f"✅ Strong signals broadcast to {sent}/{total} subscribers!")
    else:
        st.info("No strong signals (≥80% confidence) at the moment.")

st.warning("⚠️ High risk. Only take action when confidence ≥ 80%. Trade responsibly.")

st.caption("How others can join: Tell them to search your bot username → Send /start → They will receive alerts automatically.")