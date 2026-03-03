import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE E TEMA ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.05);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
    }
    h1, h2, h3 { color: #0077ff; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE FILES ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1])
    except: return 1.08

@st.cache_data(ttl=86400)
def get_metal_data_raw(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if not data.empty:
            df = data['Close'].reset_index()
            df.columns = ['Date', 'Price_Raw']
            return df
        return None
    except: return None

inizializza_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# --- LOGICA CONVERSIONE ---
# Fattori per convertire in KG (Prezzo_Ticker * Fattore = Prezzo_per_KG)
conversions = {
    "HG=F": 2.20462,      # Rame: quotato in Libbre -> 1kg = 2.20lb
    "GC=F": 32.1507,      # Oro: quotato in Once -> 1kg = 32.15oz
    "SI=F": 32.1507,      # Argento: quotato in Once
    "LIT": 1.0,           # Litio ETF (Prezzo per azione, usato come indice)
    "COB.AX": 1.0,        # Cobalto Proxy (Prezzo per azione)
    "NI=F": 2.20462,      # Nichel: quotato in Libbre
    "ALI=F": 0.001,       # Alluminio: quotato in Tonnellate -> 1kg = 0.001t
    "PA=F": 32.1507       # Palladio: Once
}

# --- DASHBOARD ---
st.title("⚡ POCKETFINANCE AI: UNIT CONVERTER")
saldo_totale = sum([(df_db[(df_db['Conto']==c) & (df_db['Tipo']=='Entrata')]['Importo'].sum() - 
                     df_db[(df_db['Conto']==c) & (df_db['Tipo']=='Uscita')]['Importo'].sum()) for c in df_conti['Conto']])

st.write(f"### 🚀 Progresso Startup: {min(saldo_totale/50000, 1.0):.1%}")
st.progress(min(max(saldo_totale/50000, 0.0), 1.0))
st.write(f"Capitale: **€ {saldo_totale:,.2f}** / € 50.000,00")

tabs = st.tabs(["➕ Movimenti", "🔍 Storico", "🤖 Chat AI", "⛏️ Metalli (€/kg)", "⚙️ Impostazioni"])

with tabs[0]: # Movimenti
    with st.form("new_op"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0)
        nota = c2.text_input("Nota")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            pd.concat([df_db, pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                      columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

with tabs[3]: # Metalli PRO
    st.subheader("⛏️ Quotazioni Reali in €/kg")
    metalli_info = {
        "Rame": "HG=F", "Oro": "GC=F", "Argento": "SI=F", 
        "Litio (Index)": "LIT", "Cobalto (Proxy)": "COB.AX", 
        "Nichel": "NI=F", "Alluminio": "ALI=F"
    }
    
    scelta = st.selectbox("Seleziona Metallo", list(metalli_info.keys()))
    ticker = metalli_info[scelta]
    rate = get_eur_usd_rate()
    dati_raw = get_metal_data_raw(ticker)
    
    if dati_raw is not None:
        fattore = conversions.get(ticker, 1.0)
        # Calcolo Prezzo Finale: (Prezzo_USD * Fattore_Conversione_KG) / Tasso_Cambio_EUR
        dati_raw['Price_EUR_KG'] = (dati_raw['Price_Raw'] * fattore) / rate
        
        prezzo_kg = float(dati_raw['Price_EUR_KG'].iloc[-1])
        
        c_m1, c_m2 = st.columns(2)
        c_m1.metric(f"Prezzo {scelta}", f"€ {prezzo_kg:.2f} / kg")
        c_m2.metric("Cambio EUR/USD", f"{rate:.4f}")
        
        fig = px.line(dati_raw, x='Date', y='Price_EUR_KG', title=f"Trend Annuale {scelta} (€/kg)")
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Nota: Ticker {ticker} convertito con fattore {fattore} per ottenere unità di misura in kg.")
    else: st.error("Dati non disponibili.")

with tabs[2]: # Chat AI
    st.subheader("🤖 AI Advisor")
    user_q = st.text_input("Chiedi all'AI...")
    if user_q:
        st.info(f"AI: Analizzando il tuo capitale di {saldo_totale}€ e i prezzi dei metalli... Suggerisco cautela negli acquisti di {scelta} se il trend è rialzista.")

with tabs[1]: # Storico
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

with tabs[4]: # Impostazioni
    new_c = st.text_input("Nuovo Conto")
    if st.button("AGGIUNGI"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
