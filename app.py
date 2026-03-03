import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE IDENTITY REACTOFINANCE ---
# Il file logo.png deve essere nella stessa cartella di questo file .py
st.set_page_config(
    page_title="ReactoFinance",
    page_icon="logo.png" if os.path.exists("logo.png") else "🧪",
    layout="wide"
)

# --- 2. TEMA DARK & NEON BLUE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.05);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 119, 255, 0.2);
    }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { 
        background-color: #0077ff; color: white; border-radius: 20px; 
        width: 100%; border: none; font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #0055ff; box-shadow: 0 0 20px #0077ff; }
    .stChatFloatingInputContainer { background-color: #0a0a0a; border-top: 1px solid #0077ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { color: #0077ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA GESTIONE DATI ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_sistema():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza Ricerca"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_rate_eurusd():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1].squeeze())
    except: return 1.10

@st.cache_data(ttl=3600)
def get_metal_price_kg(ticker, factor):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        rate = get_rate_eurusd()
        price_usd = float(data['Close'].iloc[-1].squeeze())
        return (price_usd * factor) / rate
    except: return 0.0

inizializza_sistema()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo Reale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo_attuale = entrate - uscite

# --- 4. INTERFACCIA PRINCIPALE ---
col_logo, col_titolo = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
    else:
        st.write("🧪")

with col_titolo:
    st.title("ReactoFinance AI")
    st.caption("Advanced Chemical Engineering Financial Management System")

# Monitoraggio Obiettivo Startup
st.write(f"### 🚀 Progresso Obiettivo 50.000€")
progresso = min(max(saldo_attuale / 50000, 0.0), 1.0)
st.progress(progresso)
st.write(f"Saldo Consolidato: **€ {saldo_attuale:,.2f}** | Mancano: **€ {max(50000-saldo_attuale, 0):,.2f}**")

st.markdown("---")

tabs = st.tabs(["➕ Movimenti", "🔍 Archivio", "🤖 ReactoBot AI", "⛏️ Metalli PRO", "⚙️ Setup"])

# --- TAB MOVIMENTI ---
with tabs[0]:
    with st.form("new_transaction"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Direzione", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Valore (€)", min_value=0.0, step=0.01)
        nota = c2.text_input("Descrizione (es: Materiale Laboratorio, Stipendio)")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            nuovo = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                 columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df_db, nuovo], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB ARCHIVIO ---
with tabs[1]:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("Rimuovi ID", min_value=0, step=1)
    if st.button("ELIMINA DEFINITIVAMENTE"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# --- TAB CHAT AI ---
with tabs[2]:
    st.subheader("🤖 ReactoAdvisor AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Sistema ReactoFinance pronto. Come posso ottimizzare i tuoi flussi di cassa oggi?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Chiedi analisi finanziaria o mercati..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            if "andando" in p.lower() or "startup" in p.lower():
                response = f"
