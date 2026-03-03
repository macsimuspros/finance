import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY & ICONA ---
# Caricamento forzato dell'immagine per bypassare la cache di Streamlit
icona_path = "logo.png"
if os.path.exists(icona_path):
    try:
        img_per_icona = Image.open(icona_path)
        st.set_page_config(
            page_title="ReactoFinance",
            page_icon=img_per_icona, 
            layout="wide"
        )
    except:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
else:
    st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

# --- 2. TEMA PERSONALIZZATO (DARK NEON BLUE) ---
st.markdown("""
    <style>
    /* Nasconde elementi superflui */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* Box Metriche */
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.08);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 119, 255, 0.3);
    }
    
    /* Titoli Neon */
    h1, h2, h3 { 
        color: #0077ff !important; 
        text-shadow: 0 0 12px #0077ff; 
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Bottoni */
    .stButton>button { 
        background-color: #0077ff; 
        color: white; 
        border-radius: 25px; 
        border: none; 
        font-weight: bold;
        transition: 0.4s;
        height: 3em;
    }
    .stButton>button:hover {
        background-color: #0055ff;
        box-shadow: 0 0 25px #0077ff;
        transform: scale(1.02);
    }
    
    /* Input Chat */
    .stChatFloatingInputContainer { background-color: #0a0a0a; border-top: 2px solid #0077ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE E CALCOLI ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def init_system():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Conto Principale", "Risparmi Startup", "Fondo Reagenti"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_eurusd():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1].squeeze())
    except: return 1.10

@st.cache_data(ttl=3600)
def get_metal_kg(ticker, factor):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        rate = get_eurusd()
        p_usd = float(data['Close'].iloc[-1].squeeze())
        return (p_usd * factor) / rate
    except: return 0.0

init_system()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo Globale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo_totale = entrate - uscite

# --- 4. LAYOUT SUPERIORE ---
col_logo, col_text = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    else:
        st.title("🧪")

with col_text:
    st.title("ReactoFinance")
    st.write(f"### 🚀 Capitale Startup: € {saldo_totale:,.2f} / € 50.000,00")
    prog = min(max(saldo_totale / 50000, 0.0), 1.0)
    st.progress(prog)

st.markdown("---")

tabs = st.tabs(["📊 Gestione", "🤖 ReactoChat AI", "⛏️ Market Metalli", "⚙️ Impostazioni"])

# --- TAB GESTIONE ---
with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Nuova Voce")
        with st.form("trans_form"):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            c = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            desc = st.text_input("Nota/Descrizione")
            if st.form_submit_button("REGISTRA"):
                nid = int(df_db['ID'].max() + 1) if not df_db.empty else 1
                row = pd.DataFrame([[nid, datetime.now().strftime("%Y-%m-%d"), t, c, val, desc]], columns=df_db.columns)
                pd.concat([df_db, row], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()
    with c2:
        st.subheader("🔍 Registro Storico")
        st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
        id_del = st.number_input("ID da eliminare", min_value=0, step=1)
        if st.button("ELIMINA RIGA"):
            df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB CHAT AI ---
with tabs[1]:
    st.subheader("🤖 ReactoAdvisor")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Sistema ReactoFinance pronto. Come posso aiutarti con il tuo piano quinquennale?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if p := st.chat_input("Chiedi analisi..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        with st.chat_message("assistant"):
            if "andando" in p.lower():
                r = f"Il reattore finanziario è al {prog*100:.1%}. Mancano €{max(50000-saldo_totale, 0):,.2f} per l'indipendenza della tua startup."
            else:
                r = "Dati acquisiti. Sto ottimizzando la proiezione di crescita per la tua azienda di ingegneria chimica."
            st.markdown(r)
            st.session_state.messages.append({"role": "assistant", "content": r})

# --- TAB METALLI ---
with tabs[2]:
    st.subheader("⛏️ Quotazioni Commodity (€/kg)")
    met_dict = {
        "Rame (Cu)": ["HG=F", 2.2046], 
        "Oro (Au)": ["GC=F", 32.1507], 
        "Litio (Index)": ["LTHM", 0.45],
        "Nichel (Ni)": ["NI=F", 2.2046]
    }
    s = st.selectbox("Seleziona Metallo", list(met_dict.keys()))
    price = get_metal_kg(met_dict[s][0], met_dict[s][1])
    
    m1, m2 = st.columns(2)
    m1.metric(f"Prezzo {s}", f"€ {price:.2f} / kg")
    
    hist = yf.download(met_dict[s][0], period="6mo", progress=False)['Close'].reset_index()
    fig = px.line(hist, x='Date', y='Close', title=f"Trend 6 Mesi (USD)")
    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
    st.plotly_chart(fig, use_container_width=True)

# --- TAB IMPOSTAZIONI ---
with tabs[3]:
    st.subheader("⚙️ Configurazione ReactoFinance")
    new_c = st.text_input("Aggiungi nuovo conto")
    if st.button("SALVA"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
