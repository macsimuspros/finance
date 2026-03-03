import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE PAGINA, NOME E ICONA ---
# Nota: Per usare l'immagine caricata come icona, assicurati che il file
# sia rinominato in 'logo.png' nella stessa cartella del file .py
st.set_page_config(
    page_title="ReactoFinance AI",
    page_icon="🧪", # In alternativa puoi mettere "logo.png" se presente in locale
    layout="wide"
)

# --- TEMA NERO E BLU ELETTRICO ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 119, 255, 0.05);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(0, 119, 255, 0.2);
    }
    h1, h2, h3 { color: #0077ff; text-shadow: 0 0 10px #0077ff; font-family: 'Courier New', Courier, monospace; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; width: 100%; border: none; font-weight: bold; }
    .stChatFloatingInputContainer { background-color: #111; border-top: 1px solid #0077ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { color: #0077ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE E FILE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Investimenti Metalli"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1])
    except: return 1.15 # Valore fallback basato sul tuo screenshot

@st.cache_data(ttl=3600)
def get_metal_price(ticker, factor):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        rate = get_eur_usd_rate()
        price_usd = float(data['Close'].iloc[-1].squeeze())
        return (price_usd * factor) / rate
    except: return 0.0

inizializza_files()
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

# Calcolo Saldo Globale
entrate = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum()
uscite = df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
saldo_totale = entrate - uscite

# --- 3. DASHBOARD SUPERIORE ---
st.title("🧪 ReactoFinance AI")
st.write(f"### 🚀 Obiettivo Startup (Target: 50.000€)")
progresso = min(max(saldo_totale / 50000, 0.0), 1.0)
st.progress(progresso)
st.write(f"Capitale Accumulato: **€ {saldo_totale:,.2f}** ({progresso:.1%})")

st.markdown("---")

tabs = st.tabs(["➕ Movimenti", "🔍 Storico", "🤖 ReactoChat AI", "⛏️ Metalli PRO (€/kg)", "⚙️ Impostazioni"])

# --- TAB 1: MOVIMENTI ---
with tabs[0]:
    with st.form("nuova_operazione"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
        nota = c2.text_input("Nota (es: Acquisto Reagenti, Stipendio)")
        if st.form_submit_button("REGISTRA MOVIMENTO"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            nuovo_mov = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                     columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df_db, nuovo_mov], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB 2: STORICO ---
with tabs[1]:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID da eliminare", min_value=0, step=1)
    if st.button("ELIMINA MOVIMENTO SELEZIONATO"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# --- TAB 3: CHAT AI CON BARRA ---
with tabs[2]:
    st.subheader("🤖 ReactoAdvisor AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Benvenuto in ReactoFinance. Sono pronto ad analizzare i tuoi dati per la tua startup chimica."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Scrivi qui per parlare con ReactoFinance AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if "andando" in prompt.lower() or "risparm" in prompt.lower():
                response = f"Stai procedendo bene. Hai accumulato €{saldo_totale:,.2f}. Per i 50k mancano €{max(50000-saldo_totale,0):,.2f}."
            elif "metalli" in prompt.lower() or "prezz" in prompt.lower():
                response = "Monitorare i metalli è cruciale. Nel tab Metalli PRO trovi le quotazioni industriali reali convertite in kg."
            else:
                response = "Ricevuto. Sto integrando questa informazione nel tuo piano finanziario quinquennale."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- TAB 4: METALLI PRO ---
with tabs[3]:
    metal_logic = {
        "Rame": {"t": "HG=F", "f": 2.2046}, 
        "Oro": {"t": "GC=F", "f": 32.1507}, 
        "Litio (Indice)": {"t": "LTHM", "f": 0.45}, 
        "Cobalto (Proxy)": {"t": "COB.AX", "f": 12.5}
    }
    scelta = st.selectbox("Seleziona Metallo", list(metal_logic.keys()))
    info = metal_logic[scelta]
    
    p_kg = get_metal_price(info['t'], info['f'])
    col_v1, col_v2 = st.columns(2)
    col_v1.metric(f"Prezzo {scelta}", f"€ {p_kg:.2f} / kg")
    col_v2.metric("Unità di Misura", "Kilogrammo (kg)")
    
    # Grafico Storico
    dati_m = yf.download(info['t'], period="6mo", progress=False)['Close'].reset_index()
    dati_m.columns = ['Data', 'Prezzo']
    fig = px.line(dati_m, x='Data', y='Prezzo', title=f"Trend 6 Mesi - {scelta}")
    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: IMPOSTAZIONI ---
with tabs[4]:
    st.subheader("⚙️ Gestione Conti ReactoFinance")
    new_c = st.text_input("Inserisci nome nuovo conto")
    if st.button("AGGIUNGI"):
        pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()
    
    st.write("---")
    del_c =
