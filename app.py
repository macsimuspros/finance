import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY (FIX ICONA) ---
icona_path = "logo.png"

def load_page_config():
    title = "ReactoFinance"
    if os.path.exists(icona_path):
        try:
            img = Image.open(icona_path)
            st.set_page_config(page_title=title, page_icon=img, layout="wide")
        except:
            st.set_page_config(page_title=title, page_icon="🧪", layout="wide")
    else:
        st.set_page_config(page_title=title, page_icon="🧪", layout="wide")

load_page_config()

# --- 2. CSS CUSTOM (STILE NEON) ---
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
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 4. HEADER ---
col_l, col_r = st.columns([1, 5])
with col_l:
    if os.path.exists(icona_path):
        st.image(icona_path, width=100)
with col_r:
    st.title("ReactoFinance")
    st.write(f"🚀 Obiettivo: **€ {saldo:,.2f} / € 50.000**")
    st.progress(min(max(saldo/50000, 0.0), 1.0))

tabs = st.tabs(["📊 Gestione", "🤖 Chat AI", "⛏️ Market Metalli", "⚙️ Impostazioni"])

# --- TAB METALLI (FIX VALUERROR) ---
with tabs[2]:
    st.subheader("⛏️ Quotazioni Reali (€/kg)")
    metalli = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LTHM", "Nichel": "NI=F"}
    scelta = st.selectbox("Seleziona Metallo", list(metalli.keys()))
    
    try:
        # Download dati
        data = yf.download(metalli[scelta], period="6mo", progress=False)
        if not data.empty:
            # Fix per il grafico: resettiamo l'indice e forziamo i nomi colonne
            hist = data['Close'].reset_index()
            hist.columns = ['Data_Grafico', 'Prezzo_USD']
            
            last_p = hist['Prezzo_USD'].iloc[-1]
            st.metric(f"Prezzo {scelta}", f"$ {float(last_p):,.2f}")
            
            # Grafico sicuro
            fig = px.line(hist, x='Data_Grafico', y='Prezzo_USD', title=f"Andamento {scelta}")
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Errore nel caricamento dati mercato: {e}")

# --- TAB GESTIONE ---
with tabs[0]:
    with st.form("new"):
        c1, c2 = st.columns(2)
        t = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        cnt = c1.selectbox("Conto", df_conti['Conto'].tolist())
        val = c2.number_input("Euro", min_value=0.0)
        nota = c2.text_input("Nota")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
            pd.concat([df_db, row], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB CHAT AI ---
with tabs[1]:
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input("Chiedi..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        resp = "Analisi ReactoFinance: Il tuo capitale sta reagendo bene."
        with st.chat_message("assistant"): st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})

# --- TAB IMPOSTAZIONI ---
with tabs[3]:
    add = st.text_input("Nuovo conto")
    if st.button("AGGIUNGI"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [add]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
