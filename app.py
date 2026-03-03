import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY ---
icona_path = "logo.png"
def load_config():
    title = "ReactoFinance"
    if os.path.exists(icona_path):
        try:
            img = Image.open(icona_path)
            st.set_page_config(page_title=title, page_icon=img, layout="wide")
        except:
            st.set_page_config(page_title=title, page_icon="🧪", layout="wide")
    else:
        st.set_page_config(page_title=title, page_icon="🧪", layout="wide")

load_config()

# --- 2. STILE CSS (NEON BLUE) ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.08);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 119, 255, 0.3);
    }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 12px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 25px; border: none; font-weight: bold; width: 100%; height: 3em; transition: 0.3s; }
    .stButton>button:hover { background-color: #0055ff; box-shadow: 0 0 20px #0077ff; }
    .stChatFloatingInputContainer { background-color: #0a0a0a; border-top: 2px solid #0077ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def init_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Ricerca"]}).to_csv(SETTINGS_FILE, index=False)

init_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo = entrate - uscite

# --- 4. HEADER ---
col_l, col_r = st.columns([1, 5])
with col_l:
    if os.path.exists(icona_path):
        st.image(icona_path, width=100)
with col_r:
    st.title("ReactoFinance")
    st.write(f"🚀 Obiettivo Startup: **€ {saldo:,.2f} / € 50.000**")
    st.progress(min(max(saldo/50000, 0.0), 1.0))

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Market Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE (Aggiunta & Eliminazione) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("new_entry"):
            t = st.selectbox("Tipo", ["Uscita", "Entrata"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Importo (€)", min_value=0.0, step=0.01)
