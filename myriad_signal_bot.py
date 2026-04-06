import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ====================== CREDENTIALS ======================
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
        st.markdown("<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>", unsafe_allow_html=True)

st.title("🚀 Myriad Markets 5-Min Candle Signal Bot")
st.subheader("Works on Cloud • Confidence for All • Alert ≥80%")

def send_telegram_alert(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=8)
        return True
    except:
        return False

# ====================== CLOUD-FRIENDLY DATA FETCH ======================
def get_klines(symbol):
    headers = {"User-Agent": "Mozilla/5.0"}  # Helps avoid some blocks

    # Futures first
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=5m&limit=15"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "✅ Futures"
    except Exception as e:
        pass

    # Spot fallback
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=15"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','close_time','quote_volume','trades','taker_base','taker_quote','ignore'])
                df['close'] = pd.to_numeric(df['close'])
                return df, "✅ Spot"
    except:
        pass

    return None, "❌ No data (both sources failed)"

def generate_signal(df, asset_name):
    if df is None or len(df) < 3:
        return f"**WAITING** ({asset_name})", 0, "Not enough data"
    
    current = float(df['close'].iloc[-1])
    prev = float(df['close'].iloc[-3])
    momentum = (current - prev) / prev * 100 if prev != 0 else 0
    
    if momentum > 0.25:
        return f"**STRONG BUY — MORE GREEN**", 85, f"+{momentum:.2f}%"
    elif momentum > 0.09:
        return f"**BUY — MORE GREEN**", 68, f"+{momentum:.2f}%"
    elif momentum < -0.25:
        return f"**STRONG BUY — MORE RED**", 83, f"{momentum:.2f}%"
    elif momentum < -0.09:
        return f"**BUY — MORE RED**", 70, f"{momentum:.2f}%"
    else:
        return f"**NEUTRAL — WAIT**", 50, f"{momentum:.2f}%"

coins = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "ZEC": "ZECUSDT", "PENGU": "PENGUUSDT"}

# ====================== MAIN APP ======================
if st.button("🔴 REFRESH SIGNALS NOW (Strong Only)", type="primary", use_container_width=True):
    st.rerun()

st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S UTC')}")

with st.spinner("Fetching data..."):
    alert_lines = [f"🔔 **Myriad Strong Signals** @ {datetime.now().strftime('%H:%M UTC')}\n"]
    has_strong = False

    for name, symbol in coins.items():
        st.subheader(name)
        df, status = get_klines(symbol)
        
        if df is not None:
            price = float(df['close'].iloc[-1])
            signal, conf, reason = generate_signal(df, name)
            price_str = f"${price:,.4f}" if name == "PENGU" else f"${price:,.0f}"
            
            st.metric(f"Price", price_str)
            st.markdown(f"### {signal}")
            st.progress(conf / 100)
            st.caption(f"**Confidence**: {conf}% — {reason} | {status}")
            
            if conf >= 80:
                st.success("🔥 STRONG SIGNAL — Buy on Myriad!")
                alert_lines.append(f"• **{signal} {name}** | Conf: {conf}% | {price_str}")
                has_strong = True
        else:
            st.error(f"❌ {name}: {status}")
        
        st.markdown("---")

    if has_strong:
        if send_telegram_alert("\n".join(alert_lines)):
            st.success("✅ Telegram alert sent!")
    else:
        st.info("No strong signals (≥80%) right now.")

st.warning("⚠️ Only trade when confidence ≥ 80%. This is a momentum signal tool — high risk.")

st.caption("Local works because of your IP. Cloud sometimes gets blocked by Binance. Click Refresh often.")