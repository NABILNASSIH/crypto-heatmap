import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time
from streamlit_autorefresh import st_autorefresh
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Crypto Scan Pro")
# ==========================================
# CONFIGURATION
# ==========================================
TELEGRAM_TOKEN = "8665983427:AAE_ISlSPCpfhBbMc5wH6J439phZTV67gUo"
TELEGRAM_CHAT_ID = "6338520347"

COINS_REF = {
    "TRXUSDT": 0.3293,
    "RIVERUSDT": 5.9234,
    "EDGEUSDT": 1.3956,
    "TRADOORUSDT": 8.0652,
    "BSBUSDT": 0.41253,
    "OPGUSDT": 0.3195,
    "OFCUSDT": 0.06013,
    "STUSDT": 0.07095,
    "PIPPINUSDC": 0.02559,
    "DEXEUSDT": 12.557,
    "ALEOUSDT": 0.04488,
    "AIOTUSDT": 0.042831,
    "TAOUSDT": 246.58,
    "ARIAUSDT": 0.06900,
    "COREUSDT": 0.04889,
    "BASEDUSDT": 0.13460,
    "LABUSDT": 0.68855,
    "BULLAUSDT": 0.011093,
    "ONTUSDT": 0.07976,
    "SIRENUSDT": 0.6583,
    "PENGUINUSDT": 0.002694,
    "PUNCHUSDT": 0.002785,
    "OILUSDT": 135.10,
    "OPNUSDT": 0.1765,
    "PIUSDT": 0.16786,
    "WARDUSDT": 0.003371,
    "ZAMAUSDT": 0.02823,
    "XAUTUSDT": 4686.4,
    "SENTUSDT": 0.02051,
    "GATAUSDT": 0.002192,
    "CHZUSDT": 0.04835,
    "LTCUSDT": 55.84,
    "AXSUSDT": 1.1016,
    "PERPUSDT": 0.02567,
    "SKRUSDT": 0.014896,
    "RENDERUSDT": 1.788,
    "IPUSDT": 0.5221,
    "MOVRUSDT": 2.615,
    "AMPUSDT": 0.0008814,
    "ENJUSDT": 0.06193,
    "ARUSDT": 1.923,
    "MOCAUSDT": 0.01315,
    "BEATUSDT": 0.52285,
    "AVAXUSDT": 9.324,
    "ONDOUSDT": 0.25974,
    "KTAUSDT": 0.1562,
    "RAVEUSDT": 1.1880,
    "ARBUSDT": 0.12804,
    "0GUSDT": 0.5713,
    "ZENUSDT": 6.014,

    "HYPEUSDT": 41.26,
    "AIAUSDT": 0.06051,
    "BTCUSDT": 77900.82,
    "FETUSDT": 0.2086,
    "ICPUSDT": 2.464,
    "ACHUSDT": 0.006128,
    "FWOGUSDT": 0.004555,
    "ARCSOLUSDT": 0.06700,
    "FARTCOINUSDT": 0.19837,
    "USELESSUSDT": 0.042150,
    "JELLYJELLYUSDT": 0.045171,
    "DOGEUSDT": 0.09690,
    "XVGUSDT": 0.003366,
    "FILUSDT": 0.9274,
    "ALGOUSDT": 0.10367,
    "DOTUSDT": 1.236,
    "XRPUSDT": 1.4335,
    "IOSTUSDT": 0.001080,
    "SUIUSDT": 0.9415,
    "DUSKUSDT": 0.13560,
    "SCRTUSDT": 0.11120,
    "ASTERUSDT": 0.6733,
    "TRUSTUSDT": 0.06603,
    "DCRUSDT": 19.678,
    "WLFIUSDT": 0.07733,
    "DASHUSDT": 35.68,
    "ZECUSDT": 339.39,
    "CGNUSDT": 0.002414,
    "COAIUSDT": 0.3175,
    "ALUUSDT": 0.005729,
    "ATUSDT": 0.16662,
    "ENAUSDT": 0.10960,
    "SAGAUSDT": 0.01722,
    "XLMUSDT": 0.1760,
    "HBARUSDT": 0.09060,
    "SEIUSDT": 0.06114
}

# Mémoire des alertes pour éviter le spam
if "sent_alerts" not in st.session_state:
    st.session_state.sent_alerts = {}
if "level_alerts" not in st.session_state:
    st.session_state.level_alerts = {}

# ==========================================
# FONCTIONS TECHNIQUES
# ==========================================

def fetch_coin_data(sym, ref):
    """Récupère les données pour une pièce (sans accès à Streamlit context)"""
    try:
        session = requests.Session()
        
        # 1. Prix actuel
        r = session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=3)
        r.raise_for_status()
        price = float(r.json()["price"])
        var = ((price - ref) / ref) * 100

        # 2. Récupération des niveaux (1H et 15min)
        h1_data = session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=24", timeout=3).json()
        sup_1h = min([float(c[3]) for c in h1_data])
        res_1h = max([float(c[2]) for c in h1_data])

        # 15m
        m15_data = session.get(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=16", timeout=3).json()
        sup_15m = min([float(c[3]) for c in m15_data])
        res_15m = max([float(c[2]) for c in m15_data])

        color = "#00FF00" if var > 0.10 else "#FF0000" if var < -0.10 else "#444444"
        return {
            "Coin": sym.replace("USDT",""), "Price": price, "Var": var, 
            "S1H": sup_1h, "R1H": res_1h, "S15M": sup_15m, "R15M": res_15m, "Color": color
        }
    except Exception:
        return None

def send_telegram(msg):
    """Envoie un message Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=3)
    except:
        pass

@st.cache_data(ttl=30)  # Cache de 30 secondes
def get_crypto_data():
    """Récupère les données de tous les coins en parallèle"""
    rows = []
    
    # Utiliser ThreadPoolExecutor pour paralléliser les requêtes
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_coin_data, sym, ref): sym for sym, ref in COINS_REF.items()}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                rows.append(result)
    
    return pd.DataFrame(rows)

def check_and_send_alerts(df):
    """Vérifie et envoie les alertes de supports/résistances (exécuté dans le thread principal)"""
    for _, row in df.iterrows():
        sym = row["Coin"] + "USDT"
        price = row["Price"]
        
        levels = [
            (row["S1H"], "SUPPORT 1H", "📉"), 
            (row["S15M"], "SUPPORT 15M", "📉"),
        ]

        for val, label, emoji in levels:
            diff_pct = abs((price - val) / val) * 100
            alert_key = f"{sym}_{label}"
            
            if diff_pct <= 0.2:
                if st.session_state.level_alerts.get(alert_key) != "near":
                    msg = f"{emoji} *PROXIMITÉ {label} : {sym}*\n\n💰 Prix: {price}\n🎯 Niveau: {val}\n⚡ Écart: {diff_pct:.3f}%"
                    send_telegram(msg)
                    st.session_state.level_alerts[alert_key] = "near"
            else:
                st.session_state.level_alerts[alert_key] = "clear"

# ==========================================
# INTERFACE STREAMLIT
# ==========================================

st_autorefresh(interval=60000, key="crypto_refresh")

st.title("📈 Heatmap & Scanner de Niveaux (1H / 15Min)")

df = get_crypto_data()

# Vérifier les alertes dans le thread principal (sans ScriptRunContext warning)
if not df.empty:
    check_and_send_alerts(df)

if not df.empty:
    # On affiche les niveaux 15min et 1H sur la carte
    df["Label"] = df.apply(lambda x: 
        f"<b>{x['Coin']}</b><br>{x['Price']:.4f} ({x['Var']:+.2f}%)<br>"
        f"R15M: {x['R15M']:.4f} | S15M: {x['S15M']:.4f}<br>"
        f"R1H: {x['R1H']:.4f} | S1H: {x['S1H']:.4f}", 
        axis=1)

    fig = go.Figure(go.Treemap(
        labels=df["Coin"], parents=[""] * len(df), values=[1]*len(df),
        text=df["Label"], textinfo="text",
        marker=dict(colors=df["Color"], line=dict(width=2, color="#0e1117"))
    ))
    fig.update_layout(height=850, margin=dict(t=0, l=10, r=10, b=0), paper_bgcolor="#0e1117", font=dict(color="white"))
    st.plotly_chart(fig, width="stretch")

st.write(f"Dernière analyse : {time.strftime('%H:%M:%S')} | Seuil Proximité : 0.2%")
