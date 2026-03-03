import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE E TEMA ---
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
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; width: 100%; border: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { color: #0077ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE FILE ---
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
    except: return 1.09

@st.cache_data(ttl=86400)
def get_metal_data_raw(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if not data.empty:
            # Pulizia per evitare colonne multiple (MultiIndex)
            df = data['Close'].copy()
            if isinstance(df, pd.DataFrame):
                df = df.iloc[:, 0]
            df = df.reset_index()
            df.columns = ['Date', 'Price_Raw']
            return df
        return None
    except: return None

inizializza_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# --- 3. LOGICA CONVERSIONE ---
metal_logic = {
    "Rame": {"ticker": "HG=F", "factor": 2.2046},     # Libbre a KG
    "Oro": {"ticker": "GC=F", "factor": 32.1507},    # Once a KG
    "Argento": {"ticker": "SI=F", "factor": 32.1507}, # Once a KG
    "Litio": {"ticker": "LTHM", "factor": 0.45},     # Proxy Stock a KG
    "Cobalto": {"ticker": "COB.AX", "factor": 12.5}, # Proxy Stock a KG
    "Nichel": {"ticker": "NI=F", "factor": 2.2046}    # Libbre a KG
}

# --- 4. DASHBOARD ---
st.title("⚡ POCKETFINANCE AI: SYSTEM STABLE")

# Calcolo Saldo Globale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo_totale = entrate - uscite

st.write(f"### 🚀 Progresso Startup: {min(saldo_totale/50000, 1.0):.1%}")
st.progress(min(max(saldo_totale/50000, 0.0), 1.0))

tabs = st.tabs(["➕ Movimenti", "🔍 Storico", "🤖 Chat AI", "⛏️ Metalli PRO", "⚙️ Impostazioni"])

# --- TAB MOVIMENTI ---
with tabs[0]:
    with st.form("new_op"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
        nota = c2.text_input("Nota")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            nuovo = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                 columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df_db, nuovo], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB STORICO ---
with tabs[1]:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID da eliminare", min_value=0, step=1)
    if st.button("ELIMINA"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# --- TAB CHAT AI ---
with tabs[2]:
    st.subheader("🤖 Analisi Strategica")
    st.info(f"Saldo attuale: € {saldo_totale:,.2f}. Stai monitorando i costi delle materie prime per la tua futura impresa.")

# --- TAB METALLI ---
with tabs[3]:
    st.subheader("⛏️ Quotazioni €/kg")
    scelta = st.selectbox("Seleziona Metallo", list(metal_logic.keys()))
    info = metal_logic[scelta]
    rate = get_eur_usd_rate()
    dati = get_metal_data_raw(info['ticker'])
    
    if dati is not None:
        dati['Price_EUR_KG'] = (dati['Price_Raw'] * info['factor']) / rate
        val_attuale = float(dati['Price_EUR_KG'].iloc[-1])
        
        c1, c2 = st.columns(2)
        c1.metric(f"{scelta}", f"€ {val_attuale:.2f} / kg")
        c2.metric("Cambio applicato", f"{rate:.4f} EUR/USD")
        
        fig = px.line(dati, x='Date', y='Price_EUR_KG', title=f"Trend {scelta}")
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Errore nel caricamento dati. Riprova tra pochi istanti.")

# --- TAB IMPOSTAZIONI (CORRETTO) ---
with tabs[4]:
    st.subheader("⚙️ Gestione Conti")
    
    # Aggiunta
    new_c = st.text_input("Nome nuovo conto")
    if st.button("AGGIUNGI CONTO"):
        if new_c:
            pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
            st.rerun()
            
    st.write("---")
    
    # Rimozione
    conto_da_del = st.selectbox("Seleziona conto da rimuovere", df_conti['Conto'].tolist())
    if st.button("RIMUOVI CONTO"):
        df_conti[df_conti['Conto'] != conto_da_del].to_csv(SETTINGS_FILE, index=False)
        st.rerun()
