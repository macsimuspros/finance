import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY ---
icona_path = "logo.png"
try:
    if os.path.exists(icona_path):
        img = Image.open(icona_path)
        st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
    else:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
except:
    st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

# --- 2. STILE CSS ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] { background: rgba(0, 119, 255, 0.1); border: 2px solid #0077ff; border-radius: 15px; padding: 20px; }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DATABASE CON AUTO-PULIZIA ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def clean_and_load_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
        return df
    
    df = pd.read_csv(DB_FILE)
    
    # Rimuove righe totalmente vuote
    df = df.dropna(how='all')
    
    # Se ci sono ID vuoti o corrotti, li ricalcola da 1 a N
    if df['ID'].isnull().any() or not pd.api.types.is_numeric_dtype(df['ID']):
        df = df.reset_index(drop=True)
        df['ID'] = df.index + 1
        df.to_csv(DB_FILE, index=False)
    
    return df

def init_settings():
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]}).to_csv(SETTINGS_FILE, index=False)
    return pd.read_csv(SETTINGS_FILE)

df_db = clean_and_load_db()
df_conti = init_settings()

# Calcolo Saldo
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 4. HEADER ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(icona_path): st.image(icona_path, width=100)
with col_title:
    st.title("ReactoFinance")
    st.write(f"🚀 Capitale: **€ {saldo:,.2f}** / € 50.000")
    st.progress(min(max(saldo/50000, 0.0), 1.0))

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("entry_form"):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                # Calcolo ID sicuro
                new_id = 1 if df_db.empty else int(df_db['ID'].max()) + 1
                new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
                df_db = pd.concat([df_db, new_row], ignore_index=True)
                df_db.to_csv(DB_FILE, index=False)
                st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("Inserisci ID da eliminare", min_value=1, step=1)
        if st.button("ELIMINA DEFINITIVAMENTE"):
            df_db = df_db[df_db['ID'] != id_del]
            # Dopo l'eliminazione, rinfreschiamo gli ID per evitare buchi o errori
            df_db = df_db.reset_index(drop=True)
            df_db['ID'] = df_db.index + 1
            df_db.to_csv(DB_FILE, index=False)
            st.success(f"ID {id_del} eliminato e database riordinato.")
            st.rerun()
            
        if st.button("⚠️ RESET TOTALE DATABASE"):
            pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
            st.rerun()

    with c2:
        st.subheader("🔍 Registro")
        # Visualizziamo l'ID come prima colonna per chiarezza
        cols = ['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']
        st.dataframe(df_db[cols].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB METALLI ---
with tabs[2]:
    st.subheader("⛏️ Market")
    met_map = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM"}
    scelta = st.selectbox("Metallo", list(met_map.keys()))
    try:
        m_data = yf.download(met_map[scelta], period="6mo", progress=False)
        if not m_data.empty:
            hist = m_data['Close'].reset_index()
            hist.columns = ['Data', 'Prezzo']
            st.metric(f"Prezzo {scelta}", f"$ {float(hist['Prezzo'].iloc[-1]):,.2f}")
            fig = px.line(hist, x='Data', y='Prezzo')
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
    except: st.warning("Dati offline.")

# --- TAB IMPOSTAZIONI ---
with tabs[3]:
    st.subheader("⚙️ Conti")
    nuovo_c = st.text_input("Nuovo conto")
    if st.button("AGGIUNGI"):
        if nuovo_c:
            pd.concat([df_conti, pd.DataFrame({'Conto': [nuovo_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
            st.rerun()
