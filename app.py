import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. CONFIGURAZIONE E STILE (UI/UX) ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

st.markdown("""
    <style>
    /* Sfondo sfumato professionale */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    /* Card per le metriche */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    /* Header e Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA DATI ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza"]}).to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not data.empty:
            df = data['Close'].reset_index()
            df.columns = ['Date', 'Price']
            return df
        return None
    except: return None

inizializza_files()

# --- 3. BARRA DI PROGRESSO E AI ENGINE ---
def ai_advisor(df, metallo_prezzo):
    st.subheader("🤖 AI Financial Insight")
    if df.empty:
        st.info("Inserisci dei dati per attivare l'analisi AI.")
        return

    # Calcoli per AI
    uscite_tot = df[df['Tipo'] == 'Uscita']['Importo'].sum()
    entrate_tot = df[df['Tipo'] == 'Entrata']['Importo'].sum()
    risparmio_ratio = (entrate_tot - uscite_tot) / entrate_tot if entrate_tot > 0 else 0
    
    col_ai1, col_ai2 = st.columns(2)
    
    with col_ai1:
        if risparmio_ratio > 0.2:
            st.success(f"Ottimo! Stai risparmiando il {risparmio_ratio:.0%}. Il tuo piano quinquennale è solido.")
        else:
            st.warning("Attenzione: il tasso di risparmio è basso. Riduci le uscite per non ritardare il lancio della tua startup.")

    with col_ai2:
        # Nota: Qui puoi personalizzare il consiglio in base al metallo scelto nel tab
        st.info(f"Insight Settore: L'oscillazione dei metalli suggerisce di monitorare i costi di inventario per la tua futura azienda.")

# --- 4. INTERFACCIA ---
st.title("💰 PocketFinance AI Pro")
st.caption("Engineering Financial Management System v3.0")

# --- PROGRESS BAR STARTUP ---
st.write("### 🚀 Obiettivo Startup (Capitale Target: 50.000€)")
df_tot = pd.read_csv(DB_FILE)
risparmi_startup = df_tot[(df_tot['Conto'] == 'Risparmi Startup') & (df_tot['Tipo'] == 'Entrata')]['Importo'].sum()
target = 50000
progresso = min(risparmi_startup / target, 1.0)
st.progress(progresso)
st.write(f"Hai accumulato **{risparmi_startup:.2f}€** del tuo obiettivo di {target}€ ({progresso:.1%})")

tabs = st.tabs(["➕ Movimenti", "🔍 Gestione", "🏦 Conti", "⛏️ Metalli & AI"])

with tabs[0]:
    with st.form("entry"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Conto", pd.read_csv(SETTINGS_FILE)['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0)
        nota = c2.text_input("Commento")
        if st.form_submit_button("REGISTRA"):
            df = pd.read_csv(DB_FILE)
            new_id = int(df['ID'].max() + 1) if not df.empty else 1
            new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                    columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

with tabs[1]:
    df_db = pd.read_csv(DB_FILE)
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID da eliminare", min_value=0, step=1)
    if st.button("Elimina Movimento", type="primary"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

with tabs[2]:
    st.subheader("Gestione Conti")
    # Logica semplice per aggiungere/rimuovere conti
    nuovo_c = st.text_input("Nuovo Conto")
    if st.button("Aggiungi"):
        df_c = pd.read_csv(SETTINGS_FILE)
        pd.concat([df_c, pd.DataFrame({'Conto': [nuovo_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
        st.rerun()

with tabs[3]:
    st.subheader("Mercati & Analisi AI")
    metalli = {"Rame": "HG=F", "Oro": "GC=F", "Litio": "LIT", "Cobalto": "COB.AX"}
    m_choice = st.selectbox("Seleziona Metallo", list(metalli.keys()))
    dati_m = get_metal_data(metalli[m_choice])
    
    if dati_m is not None:
        st.line_chart(dati_m.set_index('Date'))
        # Attivazione AI
        ai_advisor(df_tot, dati_m['Price'].iloc[-1])
