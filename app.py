import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY (REACTOFINANCE) ---
icona_path = "logo.png"

def load_branding():
    title = "ReactoFinance"
    if os.path.exists(icona_path):
        try:
            img = Image.open(icona_path)
            st.set_page_config(page_title=title, page_icon=img, layout="wide")
        except:
            st.set_page_config(page_title=title, page_icon="🧪", layout="wide")
    else:
        st.set_page_config(page_title=title, page_icon="🧪", layout="wide")

load_branding()

# --- 2. STILE CSS (NEON BLUE & DARK) ---
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
    .stButton>button { background-color: #0077ff; color: white; border-radius: 25px; border: none; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #0055ff; box-shadow: 0 0 20px #0077ff; transform: scale(1.02); }
    .stChatFloatingInputContainer { background-color: #0a0a0a; border-top: 2px solid #0077ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE DATABASE LOGIC ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Ricerca & Sviluppo"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_conversion_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1].squeeze())
    except: return 1.10

@st.cache_data(ttl=3600)
def get_metal_price_kg(ticker, factor):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        rate = get_conversion_rate()
        price_usd = float(data['Close'].iloc[-1].squeeze())
        return (price_usd * factor) / rate
    except: return 0.0

init_db()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo Globale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo_globale = entrate - uscite

# --- 4. LAYOUT SUPERIORE ---
col_logo, col_titolo = st.columns([1, 5])
with col_logo:
    if os.path.exists(icona_path):
        st.image(icona_path, width=100)
    else:
        st.write("# 🧪")

with col_titolo:
    st.title("ReactoFinance")
    st.write(f"### 🚀 Obiettivo Startup: € {saldo_globale:,.2f} / € 50.000,00")
    prog = min(max(saldo_globale / 50000, 0.0), 1.0)
    st.progress(prog)

st.markdown("---")

tabs = st.tabs(["📊 Gestione Operativa", "🤖 ReactoBot AI", "⛏️ Metalli PRO", "⚙️ Setup & Conti"])

# --- TAB 1: GESTIONE (INSERIMENTO E ELIMINAZIONE) ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Nuova Transazione")
        with st.form("entry_form"):
            tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
            conto = st.selectbox("Conto", df_conti['Conto'].tolist())
            importo = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Descrizione")
            if st.form_submit_button("REGISTRA"):
                new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
                new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], columns=df_db.columns)
                pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()
        
        st.markdown("---")
        st.subheader("🗑️ Elimina Movimento")
        id_del = st.number_input("ID Movimento da cancellare", min_value=0, step=1)
        if st.button("ELIMINA RIGA"):
            df_db = df_db[df_db['ID'] != id_del]
            df_db.to_csv(DB_FILE, index=False)
            st.success(f"ID {id_del} rimosso.")
            st.rerun()

    with c2:
        st.subheader("🔍 Registro Storico")
        st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: CHAT AI ---
with tabs[1]:
    st.subheader("🤖 Analisi Strategica AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Benvenuto in ReactoFinance. Come posso aiutarti oggi con la tua pianificazione finanziaria quinquennale?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if p := st.chat_input("Chiedi analisi flussi..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            if "andando" in p.lower() or "startup" in p.lower():
                r = f"Analisi: Sei al {prog*100:.1%} del tuo obiettivo startup. La tua 'reazione' finanziaria è stabile."
            else:
                r = "Dati ricevuti. Sto monitorando le variabili per la tua futura azienda chimica."
            st.markdown(r)
            st.session_state.messages.append({"role": "assistant", "content": r})

# --- TAB 3: METALLI PRO (€/kg) ---
with tabs[2]:
    st.subheader("⛏️ Quotazioni Commodity Reali")
    met_data = {
        "Rame (Cu)": ["HG=F", 2.2046], "Oro (Au)": ["GC=F", 32.1507], 
        "Litio (Index)": ["LTHM", 0.45], "Nichel (Ni)": ["NI=F", 2.2046]
    }
    s_met = st.selectbox("Seleziona Metallo", list(met_data.keys()))
    price_kg = get_metal_price_kg(met_data[s_met][0], met_data[s_met][1])
    
    m1, m2 = st.columns(2)
    m1.metric(f"Prezzo {s_met}", f"€ {price_kg:.2f} / kg")
    
    try:
        hist_data = yf.download(met_data[s_met][0], period="6mo", progress=False)['Close'].reset_index()
        hist_data.columns = ['Data', 'Valore']
        fig = px.line(hist_data, x='Data', y='Valore', title=f"Andamento 6 Mesi {s_met} (USD)")
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
        st.plotly_chart(fig, use_container_width=True)
    except: st.error("Errore caricamento grafico.")

# --- TAB 4: SETUP CONTI ---
with tabs[3]:
    st.subheader("⚙️ Configurazione Conti")
    col_add, col_del = st.columns(2)
    with col_add:
        new_c = st.text_input("Nome nuovo conto")
        if st.button("AGGIUNGI CONTO"):
            if new_c:
                pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
                st.rerun()
    with col_del:
        c_del = st.selectbox("Seleziona conto da rimuovere", df_conti['Conto'].tolist())
        if st.button("ELIMINA CONTO"):
            df_conti = df_conti[df_conti['Conto'] != c_del]
            df_conti.to_csv(SETTINGS_FILE, index=False)
            st.rerun()
