import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE E TEMA NEON ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.1);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 119, 255, 0.3);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #0a0a0a;
        border: 1px solid #0077ff;
        color: #0077ff;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #0077ff !important; color: white !important; }
    h1, h2, h3 { color: #0077ff; text-shadow: 0 0 12px #0077ff; font-family: 'Roboto Mono', monospace; }
    .stButton>button {
        background-color: #0077ff; color: white; border-radius: 20px; 
        border: none; font-weight: bold; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { box-shadow: 0 0 20px #0077ff; background-color: #0055ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA FILE E DATABASE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1])
    except: return 1.08

@st.cache_data(ttl=86400)
def get_metal_data_adv(ticker):
    try:
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if not data.empty:
            df = data['Close'].reset_index()
            df.columns = ['Date', 'Price_USD']
            return df
        return None
    except: return None

inizializza_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

def calcola_saldo(conto_nome):
    entrate = df_db[(df_db['Conto'] == conto_nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    uscite = df_db[(df_db['Conto'] == conto_nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return entrate - uscite

# --- 3. DASHBOARD SUPERIORE ---
st.title("⚡ POCKETFINANCE AI PRO")
st.caption("Ingegneria Chimica & Future Startup Strategy")

# Calcolo risparmi totali per barra di progresso
saldo_totale = sum([calcola_saldo(c) for c in df_conti['Conto']])
target_startup = 50000
progresso = min(max(saldo_totale / target_startup, 0.0), 1.0)

st.write(f"### 🚀 Obiettivo Startup: {progresso:.1%}")
st.progress(progresso)
st.write(f"Capitale Consolidato: **€ {saldo_totale:,.2f}** / € 50.000,00")

# Griglia Conti con Saldo
st.write("---")
cols = st.columns(len(df_conti))
for i, row in df_conti.iterrows():
    s = calcola_saldo(row['Conto'])
    cols[i].metric(row['Conto'], f"€ {s:.2f}")

st.write("---")

# --- 4. TABS PRINCIPALI ---
tab_mov, tab_hist, tab_ai, tab_met, tab_set = st.tabs([
    "➕ Movimenti", "🔍 Storico", "🤖 Chat AI", "⛏️ Metalli PRO", "⚙️ Impostazioni"
])

# -- TAB 1: INSERIMENTO --
with tab_mov:
    with st.form("new_op"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
        nota = c2.text_input("Commento (es. Acquisto Litio, Borsa di studio)")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                    columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# -- TAB 2: STORICO E MODIFICA --
with tab_hist:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID Movimento da gestire", min_value=0, step=1)
    if st.button("ELIMINA MOVIMENTO", type="primary"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# -- TAB 3: CHAT AI ADVISOR --
with tab_ai:
    st.subheader("🤖 Financial Advisor Bot")
    user_q = st.text_input("Fai una domanda alla tua AI...")
    if user_q:
        if "startup" in user_q.lower() or "obiettivo" in user_q.lower():
            mancanti = target_startup - saldo_totale
            st.info(f"AI: Ti mancano ancora {mancanti:.2f}€ per il tuo obiettivo. Con il tuo attuale risparmio, stiamo analizzando il tempo stimato...")
        elif "metalli" in user_q.lower():
            st.info("AI: I prezzi dei metalli come Litio e Cobalto influenzano i costi della tua futura startup chimica. Monitora il tab Metalli PRO.")
        else:
            st.write("AI: Sto processando i dati dei tuoi conti per darti una risposta pertinente.")

# -- TAB 4: METALLI PRO (CONVERSIONE EUR/USD) --
with tab_met:
    st.subheader("⛏️ Mercato Commodity Strategiche")
    metalli_ticker = {
        "Rame": "HG=F", "Oro": "GC=F", "Argento": "SI=F", 
        "Litio (Proxy)": "LIT", "Cobalto (Proxy)": "COB.AX", 
        "Nichel": "NI=F", "Palladio": "PA=F", "Alluminio": "ALI=F"
    }
    
    scelta_m = st.selectbox("Seleziona Metallo", list(metalli_ticker.keys()))
    rate = get_eur_usd_rate()
    dati_m = get_metal_data_adv(metalli_ticker[scelta_m])
    
    if dati_m is not None:
        dati_m['Price_EUR'] = dati_m['Price_USD'] / rate
        ultimo_usd = float(dati_m['Price_USD'].iloc[-1])
        ultimo_eur = float(dati_m['Price_EUR'].iloc[-1])
        
        m_col1, m_col2 = st.columns(2)
        m_col1.metric("Prezzo USD", f"$ {ultimo_usd:.2f}")
        m_col2.metric("Prezzo EUR", f"€ {ultimo_eur:.2f}")
        
        fig = px.line(dati_m, x='Date', y=['Price_USD', 'Price_EUR'], 
                      title=f"Trend Annuale {scelta_m}",
                      color_discrete_map={"Price_USD": "#ff4b4b", "Price_EUR": "#0077ff"})
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff', hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Dati temporaneamente non disponibili.")

# -- TAB 5: IMPOSTAZIONI CONTI --
with tab_set:
    st.subheader("Configurazione Conti")
    new_c_name = st.text_input("Aggiungi Nome Conto")
    if st.button("AGGIUNGI"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [new_c_name]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
    
    st.write("---")
    del_c_name = st.selectbox("Elimina Conto", df_conti['Conto'].tolist())
    if st.button("ELIMINA CONTO", type="primary"):
        df_conti[df_conti['Conto'] != del_c_name].to_csv(SETTINGS_FILE, index=False)
        st.rerun()
