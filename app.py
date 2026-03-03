import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY (Sempre per prima) ---
def setup_page():
    icona_path = "logo.png"
    try:
        if os.path.exists(icona_path):
            img = Image.open(icona_path)
            st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
        else:
            st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
    except:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

setup_page()

# --- 2. STILE CSS NEON ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] { background: rgba(0, 119, 255, 0.1); border: 2px solid #0077ff; border-radius: 15px; padding: 20px; }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; height: 3em; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border-radius: 10px 10px 0 0; color: white; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #0077ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INIZIALIZZAZIONE DATABASE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def get_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
        return df
    df = pd.read_csv(DB_FILE)
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
    df = df.reset_index(drop=True)
    df['ID'] = df.index + 1
    return df

def get_settings():
    if not os.path.exists(SETTINGS_FILE) or os.stat(SETTINGS_FILE).st_size == 0:
        df = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]})
        df.to_csv(SETTINGS_FILE, index=False)
        return df
    return pd.read_csv(SETTINGS_FILE)

df_db = get_db()
df_conti = get_settings()

# Calcolo Saldo
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 4. INTERFACCIA PRINCIPALE ---
st.title("🧪 ReactoFinance")
st.write(f"🚀 Obiettivo Startup: **€ {saldo:,.2f}** / € 50.000")
st.progress(min(max(saldo/50000, 0.0), 1.0))

# I TABS sono definiti fuori da ogni condizione per garantire che non spariscano
tab1, tab2, tab3, tab4 = st.tabs(["📊 GESTIONE", "🤖 CHAT AI", "⛏️ MERCATO", "⚙️ IMPOSTAZIONI"])

# --- TAB 1: GESTIONE ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("add_form"):
            t = st.selectbox("Tipo", ["Uscita", "Entrata"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Euro", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("SALVA"):
                new_row = pd.DataFrame([[len(df_db)+1, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
                pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()
        
        st.markdown("---")
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("ID Movimento", min_value=1, step=1)
        if st.button("ELIMINA"):
            df_db = df_db.drop(df_db[df_db['ID'] == id_del].index)
            df_db.to_csv(DB_FILE, index=False)
            st.rerun()

    with c2:
        st.subheader("🔍 Registro")
        st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: CHAT AI (Ripristinata) ---
with tab2:
    st.subheader("🤖 ReactoBot AI")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
        
    if prompt := st.chat_input("Chiedi aiuto per la tua startup..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        response = f"Analisi ReactoFinance: Il tuo saldo attuale è di € {saldo:.2f}. Per la tua azienda di ingegneria chimica, questo rappresenta un ottimo punto di partenza."
        with st.chat_message("assistant"): st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- TAB 3: MERCATO ---
with tab3:
    st.subheader("⛏️ Commodities")
    scelta = st.selectbox("Metallo", ["Rame", "Oro", "Litio"])
    try:
        # Codice grafico semplificato per evitare crash
        tickers = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM"}
        data = yf.download(tickers[scelta], period="1mo", progress=False)
        if not data.empty:
            st.line_chart(data['Close'])
        else: st.warning("Dati non disponibili al momento.")
    except: st.error("Errore connessione mercati.")

# --- TAB 4: IMPOSTAZIONI (Ripristinata) ---
with tab4:
    st.subheader("⚙️ Setup Conti")
    nuovo = st.text_input("Aggiungi nuovo conto")
    if st.button("AGGIUNGI"):
        if nuovo:
            pd.concat([df_conti, pd.DataFrame({'Conto': [nuovo]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
            st.rerun()
    
    st.markdown("---")
    st.subheader("🆘 Emergenza")
    if st.button("RESET TOTALE DATABASE"):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
        st.rerun()
