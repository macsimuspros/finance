import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE E TEMA ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.05);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
    }
    h1, h2, h3 { color: #0077ff; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; width: 100%; border: none; }
    .stChatFloatingInputContainer { background-color: #111; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE FILE E DATI ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1])
    except: return 1.10

@st.cache_data(ttl=3600)
def get_metal_price(ticker, factor):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        rate = get_eur_usd_rate()
        return (float(data['Close'].iloc[-1]) * factor) / rate
    except: return 0.0

inizializza_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo
saldo_totale = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 3. DASHBOARD SUPERIORE ---
st.title("⚡ POCKETFINANCE AI PRO")
st.write(f"### 🚀 Progresso Startup: {min(saldo_totale/50000, 1.0):.1%}")
st.progress(min(max(saldo_totale/50000, 0.0), 1.0))

tabs = st.tabs(["➕ Movimenti", "🔍 Storico", "🤖 CHAT AI", "⛏️ Metalli PRO", "⚙️ Impostazioni"])

# --- TAB 1: MOVIMENTI ---
with tabs[0]:
    with st.form("new_op"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
        nota = c2.text_input("Nota")
        if st.form_submit_button("REGISTRA"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            pd.concat([df_db, pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                      columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB 2: STORICO ---
with tabs[1]:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID da eliminare", min_value=0, step=1)
    if st.button("ELIMINA"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# --- TAB 3: CHAT AI (CON BARRA DI CONVERSAZIONE) ---
with tabs[2]:
    st.subheader("🤖 Conversa con il tuo Financial Advisor")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Ciao! Sono la tua AI. Come posso aiutarti con i tuoi 50k per la startup oggi?"}]

    # Visualizza messaggi precedenti
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Barra di input per conversare
    if prompt := st.chat_input("Chiedi aiuto per i tuoi risparmi o i metalli..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Logica di risposta AI
        with st.chat_message("assistant"):
            response = ""
            if "andando" in prompt.lower() or "risparm" in prompt.lower():
                mancanti = 50000 - saldo_totale
                response = f"Stai andando bene! Hai accumulato €{saldo_totale:,.2f}. Ti mancano €{max(mancanti, 0):,.2f} per l'obiettivo startup."
            elif "metalli" in prompt.lower() or "prezz" in prompt.lower():
                response = "I mercati sono volatili. Ti consiglio di controllare il tab Metalli PRO per vedere le quotazioni in €/kg aggiornate."
            else:
                response = "Ricevuto. Sto monitorando i tuoi flussi di cassa e i prezzi delle commodity chimiche per ottimizzare il tuo piano quinquennale."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- TAB 4: METALLI PRO ---
with tabs[3]:
    metal_logic = {"Rame": {"t": "HG=F", "f": 2.2046}, "Oro": {"t": "GC=F", "f": 32.1507}, 
                   "Litio": {"t": "LTHM", "f": 0.45}, "Cobalto": {"t": "COB.AX", "f": 12.5}}
    scelta = st.selectbox("Seleziona Metallo", list(metal_logic.keys()))
    info = metal_logic[scelta]
    
    # Prezzo in tempo reale
    p_kg = get_metal_price(info['t'], info['f'])
    st.metric(f"Prezzo {scelta} Reale", f"€ {p_kg:.2f} / kg")
    
    # Grafico (Fallback veloce)
    dati = yf.download(info['t'], period="1mo", progress=False)['Close'].reset_index()
    dati.columns = ['Date', 'Price']
    fig = px.line(dati, x='Date', y='Price', title=f"Trend Mensile {scelta}")
    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: IMPOSTAZIONI ---
with tabs[4]:
    st.subheader("⚙️ Gestione Conti")
    new_c = st.text_input("Nome nuovo conto")
    if st.button("AGGIUNGI CONTO"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
    
    conto_del = st.selectbox("Rimuovi conto", df_conti['Conto'].tolist())
    if st.button("RIMUOVI"):
        df_conti[df_conti['Conto'] != conto_del].to_csv(SETTINGS_FILE, index=False)
        st.rerun()
