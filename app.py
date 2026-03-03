import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY ---
icona_path = "logo.png"
if os.path.exists(icona_path):
    try:
        img = Image.open(icona_path)
        st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
    except:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
else:
    st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

# --- 2. STILE CSS ---
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
    .stButton>button { background-color: #0077ff; color: white; border-radius: 25px; border: none; font-weight: bold; width: 100%; height: 3em; }
    .stButton>button:hover { background-color: #0055ff; box-shadow: 0 0 20px #0077ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE FILE E DATI ---
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

# Calcolo Saldo Totale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo = entrate - uscite

# --- 4. HEADER ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(icona_path):
        st.image(icona_path, width=100)
with col_title:
    st.title("ReactoFinance")
    st.write(f"### 🚀 Capitale: € {saldo:,.2f} / € 50.000,00")
    st.progress(min(max(saldo/50000, 0.0), 1.0))

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE (CON ELIMINAZIONE) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Inserisci")
        with st.form("form_add"):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                # FIX ERRORE VALUEERROR: gestiamo il caso database vuoto
                new_id = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                nuova_riga = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
                pd.concat([df_db, nuova_riga], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("ID da rimuovere", min_value=0, step=1)
        if st.button("ELIMINA DEFINITIVAMENTE"):
            df_db = df_db[df_db['ID'] != id_del]
            df_db.to_csv(DB_FILE, index=False)
            st.success(f"Movimento {id_del} eliminato!")
            st.rerun()

    with c2:
        st.subheader("🔍 Registro Movimenti")
        st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB METALLI (FIX GRAFICO) ---
with tabs[2]:
    st.subheader("⛏️ Quotazioni Commodity")
    met_map = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM", "Nichel": "NI=F"}
    scelta = st.selectbox("Metallo", list(met_map.keys()))
    try:
        data = yf.download(met_map[scelta], period="6mo", progress=False)
        if not data.empty:
            hist = data['Close'].reset_index()
            # Forziamo i nomi colonne per evitare errori px.line
            hist.columns = ['Data', 'Prezzo']
            st.metric(f"Prezzo {scelta}", f"$ {float(hist['Prezzo'].iloc[-1]):,.2f}")
            fig = px.line(hist, x='Data', y='Prezzo', title=f"Trend {scelta}")
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Errore mercati: {e}")

# --- TAB IMPOSTAZIONI ---
with tabs[3]:
    st.subheader("⚙️ Gestione Conti")
    col_a, col_b = st.columns(2)
    with col_a:
        nuovo_c = st.text_input("Aggiungi Conto")
        if st.button("AGGIUNGI"):
            if nuovo_c:
                pd.concat([df_conti, pd.DataFrame({'Conto': [nuovo_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
                st.rerun()
    with col_b:
        c_del = st.selectbox("Elimina Conto", df_conti['Conto'].tolist())
        if st.button("RIMUOVI"):
            df_conti = df_conti[df_conti['Conto'] != c_del]
            df_conti.to_csv(SETTINGS_FILE, index=False)
            st.rerun()
