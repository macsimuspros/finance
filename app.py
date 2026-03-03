import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="PocketFinance AI Pro", layout="wide")

DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

# --- FUNZIONI DATI ---
def inizializza_file():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza"]}).to_csv(SETTINGS_FILE, index=False)

def get_conti():
    return pd.read_csv(SETTINGS_FILE)['Conto'].tolist()

def aggiungi_conto(nome):
    df = pd.read_csv(SETTINGS_FILE)
    if nome not in df['Conto'].values:
        nuovo = pd.concat([df, pd.DataFrame({'Conto': [nome]})], ignore_index=True)
        nuovo.to_csv(SETTINGS_FILE, index=False)

def elimina_conto(nome):
    df = pd.read_csv(SETTINGS_FILE)
    df = df[df['Conto'] != nome]
    df.to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        return data['Close']
    except: return None

# Inizializzazione
inizializza_file()

# --- INTERFACCIA ---
st.title("💰 PocketFinance AI Pro")

tab_ins, tab_filt, tab_conti, tab_metalli = st.tabs(["➕ Movimenti", "🔍 Gestione/Ricerca", "🏦 Gestione Conti", "⛏️ Metalli"])

# --- TAB INSERIMENTO ---
with tab_ins:
    with st.form("new_entry"):
        col1, col2 = st.columns(2)
        tipo = col1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = col2.selectbox("Conto", get_conti())
        importo = st.number_input("Importo (€)", min_value=0.0)
        nota = st.text_input("Nota/Commento")
        if st.form_submit_button("REGISTRA"):
            df = pd.read_csv(DB_FILE)
            new_id = len(df) + 1
            nuova_riga = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d %H:%M"), tipo, conto, importo, nota]], 
                                      columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            pd.concat([df, nuova_riga], ignore_index=True).to_csv(DB_FILE, index=False)
            st.success("Registrato!")

# --- TAB RICERCA, MODIFICA E CANCELLAZIONE ---
with tab_filt:
    df = pd.read_csv(DB_FILE)
    if not df.empty:
        st.subheader("Storico e Modifiche")
        search = st.text_input("Cerca parola chiave...")
        filtered_df = df[df['Nota'].str.contains(search, case=False, na=False)] if search else df
        
        st.dataframe(filtered_df, use_container_width=True)
        
        st.divider()
        st.write("### Azioni su Movimento")
        id_to_edit = st.number_input("Inserisci l'ID della riga da gestire", min_value=1, step=1)
        
        c1, c2 = st.columns(2)
        if c1.button("Elimina Movimento", type="primary"):
            df = df[df['ID'] != id_to_edit]
            df.to_csv(DB_FILE, index=False)
            st.rerun()
            
        if c2.button("Modifica (Sperimentale)"):
            st.info("Per modificare: elimina la riga errata e inseriscine una nuova corretta.")
    else:
        st.info("Nessun dato.")

# --- TAB GESTIONE CONTI ---
with tab_conti:
    st.subheader("I tuoi conti")
    conti_attuali = get_conti()
    for c in conti_attuali:
        col_c1, col_c2 = st.columns([3, 1])
        col_c1.write(f"🏦 {c}")
        if col_c2.button(f"Elimina {c}", key=c):
            elimina_conto(c)
            st.rerun()
            
    new_c = st.text_input("Aggiungi nuovo conto (es. 'Postepay', 'Broker')")
    if st.button("Crea Conto"):
        aggiungi_conto(new_c)
        st.rerun()

# --- TAB METALLI ---
with tab_metalli:
    st.subheader("Mercati Materiali Strategici")
    metalli_ticker = {
        "Rame (Copper)": "HG=F",
        "Oro (Gold)": "GC=F",
        "Argento (Silver)": "SI=F",
        "Litio (LIT ETF)": "LIT",
        "Cobalto (COB)": "COB=F", 
        "Nichel (Nickel)": "NI=F"
    }
    scelta = st
