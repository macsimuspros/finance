import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- 1. THEME & UI (NERO E BLU ELETTRICO) ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] {
        background: rgba(0, 255, 255, 0.05);
        border: 2px solid #0077ff;
        border-radius: 15px;
        padding: 20px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111;
        border: 1px solid #0077ff;
        color: #0077ff;
        border-radius: 10px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #0077ff !important; color: white !important; }
    h1, h2, h3 { color: #0077ff; text-shadow: 0 0 10px #0077ff; }
    .stButton>button {
        background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGICA DATA E FILE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

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

# --- 3. LOGICA CALCOLI ---
df_db = pd.read_csv(DB_FILE)
df_conti = pd.read_csv(SETTINGS_FILE)

def calcola_saldo_conto(conto_nome):
    entrate = df_db[(df_db['Conto'] == conto_nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    uscite = df_db[(df_db['Conto'] == conto_nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return entrate - uscite

# --- 4. INTERFACCIA ---
st.title("⚡ PocketFinance AI: Engineering Edition")

# --- BARRA PROGRESSO STARTUP ---
st.write("### 🚀 Obiettivo Startup (Target: 50.000€)")
risparmi_totali = sum([calcola_saldo_conto(c) for c in df_conti['Conto']])
progresso = min(max(risparmi_totali / 50000, 0.0), 1.0)
st.progress(progresso)
st.write(f"Capitale Attuale: **{risparmi_totali:.2f}€** / 50.000€ ({progresso:.1%})")

# --- VISUALIZZAZIONE CONTI (GRID) ---
st.write("### 🏦 I Tuoi Conti")
cols_conti = st.columns(len(df_conti))
for i, riga in df_conti.iterrows():
    saldo = calcola_saldo_conto(riga['Conto'])
    cols_conti[i].metric(riga['Conto'], f"{saldo:.2f} €")

st.markdown("---")

tabs = st.tabs(["➕ Movimenti", "🔍 Storico & Modifica", "🤖 Chat AI", "⛏️ Metalli Strategici", "⚙️ Gestione Conti"])

# --- TAB 1: INSERIMENTO ---
with tabs[0]:
    with st.form("new_entry"):
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = c1.selectbox("Seleziona Conto", df_conti['Conto'].tolist())
        importo = c2.number_input("Importo (€)", min_value=0.0)
        nota = c2.text_input("Commento (es: Reagenti, Cobalto, Libri)")
        if st.form_submit_button("REGISTRA MOVIMENTO"):
            new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
            new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), tipo, conto, importo, nota]], 
                                    columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
            st.rerun()

# --- TAB 2: STORICO ---
with tabs[1]:
    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    id_del = st.number_input("ID da eliminare", min_value=0, step=1)
    if st.button("ELIMINA MOVIMENTO", type="primary"):
        df_db[df_db['ID'] != id_del].to_csv(DB_FILE, index=False)
        st.rerun()

# --- TAB 3: CHAT AI ADVISOR ---
with tabs[2]:
    st.subheader("🤖 Conversa con l'AI Finanziaria")
    user_msg = st.text_input("Chiedi un consiglio (es: 'Come sto andando?')")
    if user_msg:
        if "andando" in user_msg.lower() or "consiglio" in user_msg.lower():
            if risparmi_totali > 0:
                st.info(f"AI: Al momento hai {risparmi_totali:.2f}€. Per la tua startup chimica suggerisco di mantenere le uscite sotto il 30% delle entrate.")
            else:
                st.warning("AI: Il saldo è zero o negativo. Inizia a registrare entrate per finanziare la tua idea!")
        else:
            st.write("AI: Sto analizzando i mercati dei metalli e le tue spese per darti una risposta tecnica...")

# --- TAB 4: METALLI (COMPLETO) ---
with tabs[3]:
    metalli = {
        "Rame": "HG=F", "Oro": "GC=F", "Argento": "SI=F", 
        "Litio (LIT)": "LIT", "Cobalto (Proxy)": "COB.AX", 
        "Nichel": "NI=F", "Palladio": "PA=F"
    }
    scelta = st.selectbox("Seleziona Materiale", list(metalli.keys()))
    dati_m = get_metal_data(metalli[scelta])
    if dati_m is not None:
        fig = px.line(dati_m, x='Date', y='Price', title=f"Prezzo {scelta} (USD)")
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
        st.plotly_chart(fig, use_container_width=True)
    else: st.error("Dati non disponibili.")

# --- TAB 5: GESTIONE CONTI ---
with tabs[4]:
    st.subheader("Crea o Elimina i tuoi Conti")
    nuovo_c = st.text_input("Nome nuovo conto")
    if st.button("AGGIUNGI CONTO"):
        if nuovo_c:
            pd.concat([df_conti, pd.DataFrame({'Conto': [nuovo_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
            st.rerun()
    
    conto_del = st.selectbox("Seleziona conto da eliminare", df_conti['Conto'].tolist())
    if st.button("ELIMINA CONTO SELEZIONATO"):
        df_conti[df_conti['Conto'] != conto_del].to_csv(SETTINGS_FILE, index=False)
        st.rerun()
