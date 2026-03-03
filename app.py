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

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("entry_form"):
            t = st.selectbox("Tipo", ["Uscita", "Entrata"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                new_id = len(df_db) + 1
                new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
                df_db = pd.concat([df_db, new_row], ignore_index=True)
                df_db.to_csv(DB_FILE, index=False)
                st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("ID da eliminare", min_value=1, step=1)
        if st.button("ELIMINA DEFINITIVAMENTE"):
            df_db = df_db[df_db['ID'] != id_del]
            # Riordina gli ID dopo l'eliminazione per evitare errori futuri
            df_db = df_db.reset_index(drop=True)
            df_db['ID'] = df_db.index + 1
            df_db.to_csv(DB_FILE, index=False)
            st.success(f"ID {id_del} rimosso e database riallineato.")
            st.rerun()
            
        if st.button("⚠️ RESET TOTALE"):
            pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
            st.rerun()

    with c2:
        st.subheader("🔍 Registro")
        st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB METALLI ---
with tabs[2]:
    st.subheader("⛏️ Market Commodities")
    metalli = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM"}
    scelta = st.selectbox("Metallo", list(metalli.keys()))
    try:
        m_data = yf.download(metalli[scelta], period="6mo", progress=False)
        if not m_data.empty:
            hist = m_data['Close'].reset_index()
            hist.columns = ['Data', 'Prezzo']
            st.metric(f"Prezzo {scelta}", f"$ {float(hist['Prezzo'].iloc[-1]):,.2f}")
            fig = px.line(hist, x='Data', y='Prezzo')
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
    except: st.warning("Connessione ai mercati fallita.")
