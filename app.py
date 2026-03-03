import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY (REACTOFINANCE) ---
icona_path = "logo.png"
try:
    if os.path.exists(icona_path):
        img = Image.open(icona_path)
        st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
    else:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
except:
    st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

# --- 2. STILE CSS NEON ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] { background: rgba(0, 119, 255, 0.1); border: 2px solid #0077ff; border-radius: 15px; padding: 20px; }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DATABASE CON AUTO-RIPARAZIONE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def repair_and_load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
        return df
    
    df = pd.read_csv(DB_FILE)
    
    # PULIZIA: Rimuove righe totalmente vuote o con Tipo/Importo mancante
    df = df.dropna(subset=['Tipo', 'Importo'])
    
    # RIPARAZIONE ID: Se ci sono ID "None" o corrotti, li ricalcola da 1 a N
    df = df.reset_index(drop=True)
    df['ID'] = df.index + 1
    
    # Assicura che l'Importo sia numerico (evita TypeError nel saldo)
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
    
    df.to_csv(DB_FILE, index=False)
    return df

def init_settings():
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]}).to_csv(SETTINGS_FILE, index=False)
    return pd.read_csv(SETTINGS_FILE)

# Caricamento sicuro
df_db = repair_and_load_db()
df_conti = init_settings()

# Calcolo Saldo (Senza rischio TypeError)
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo = entrate - uscite

# --- 4. HEADER ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(icona_path): st.image(icona_path, width=100)
with col_title:
    st.title("ReactoFinance")
    st.write(f"🚀 Capitale Startup: **€ {saldo:,.2f}** / € 50.000")
    st.progress(min(max(saldo/50000, 0.0), 1.0))
