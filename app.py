import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY ---
icona_path = "logo.png"
def setup_branding():
    try:
        if os.path.exists(icona_path):
            img = Image.open(icona_path)
            st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
        else:
            st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
    except:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

setup_branding()

# --- 2. STILE CSS ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.1);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
    }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE DATABASE (CORRETTA) ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def init_files():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE) or os.stat(SETTINGS_FILE).st_size == 0:
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Ricerca"]}).to_csv(SETTINGS_FILE, index=False)

init_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo Sicuro
try:
    entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
    uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
    saldo = entrate - uscite
except:
    saldo = 0.0

# --- 4. INTERFACCIA ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(icona_path):
        st.image(icona_path, width=100)
with col_title:
    st.title("ReactoFinance")
    st.write(f"🚀 Capitale: **€ {saldo:,.2f} / € 50.000**")
    st.progress(min(max(saldo/50000, 0.0), 1.0))

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE (FIX ELIMINA/AGGIUNGI) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("entry_form"):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist() if not df_conti.empty else ["Principale"])
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Nota/Descrizione")
            if st.form_submit_button("REGISTRA"):
                # FIX DEFINITIVO PER VALUEERROR
                if df_db.empty:
                    new_id = 1
                else:
                    try:
                        new_id = int(df_db['ID'].max()) + 1
                    except:
                        new_id = 1
                
                new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
                pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("ID da eliminare", min_value=0, step=1)
        if st.button("ELIMINA DEFINITIVAMENTE"):
            df_db = df_db[df_db['ID'] != id_del]
            df_db.to_csv(DB_FILE, index=False)
            st.success("Operazione eseguita.")
            st.rerun()

    with c2:
        st.subheader("🔍 Registro")
        st.dataframe(df_db.sort_values("ID", ascending=False) if not df_db.empty else df_db, use_container_width=True, hide_index=True)

# --- TAB METALLI (FIX GRAFICO) ---
with tabs[2]:
    st.subheader("⛏️ Commodities Market")
    met_map = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM"}
    scelta = st.selectbox("Seleziona", list(met_map.keys()))
    try:
        m_data = yf.download(met_map[scelta], period="6mo", progress=False)
        if not m_data.empty:
            hist = m_data['Close'].reset_index()
            hist.columns = ['Data', 'Prezzo']
            st.metric(f"Prezzo {scelta}", f"$ {float(hist['Prezzo'].iloc[-1]):,.2f}")
            fig = px.line(hist, x='Data', y='Prezzo')
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.warning("Dati di mercato temporaneamente non disponibili.")

# --- TAB IMPOSTAZIONI ---
with tabs[3]:
    st.subheader("⚙️ Conti")
    col_a, col_b = st.columns(2)
    with col_a:
        nuovo_c = st.text_input("Nome conto")
        if st.button("AGGIUNGI"):
            if nuovo_c:
                new_c_df = pd.DataFrame({'Conto': [nuovo_c]})
                pd.concat([df_conti, new_c_df], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
                st.rerun()
    with col_b:
        c_del = st.selectbox("Elimina", df_conti['Conto'].tolist())
        if st.button("RIMUOVI"):
            df_conti = df_conti[df_conti['Conto'] != c_del]
            df_conti.to_csv(SETTINGS_FILE, index=False)
            st.rerun()
