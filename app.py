import streamlit as st
import pandas as pd
import os
from datetime import datetime
import yfinance as yf
import plotly.express as px

# --- CONFIGURAZIONE ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

# Funzione critica: Inizializza i file SOLO se non esistono affatto
def init_storage():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
    
    if not os.path.exists(SETTINGS_FILE):
        df_c = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]})
        df_c.to_csv(SETTINGS_FILE, index=False)

# Esegui inizializzazione
init_storage()

# Caricamento dati (usiamo try-except per evitare crash se il file è corrotto)
try:
    df_db = pd.read_csv(DB_FILE)
    df_db['Importo'] = pd.to_numeric(df_db['Importo'], errors='coerce').fillna(0.0)
except:
    df_db = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])

try:
    df_conti = pd.read_csv(SETTINGS_FILE)
except:
    df_conti = pd.DataFrame({'Conto': ["Principale"]})

# --- INTERFACCIA ---
st.title("🧪 ReactoFinance AI")

# Calcolo Saldo
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()
st.metric("Capitale Accumulato", f"€ {saldo:,.2f}", delta=f"Target: € 50.000")

tabs = st.tabs(["📊 Gestione", "🤖 AI Advisor", "⚙️ Setup"])

with tabs[0]:
    with st.form("nuovo_movimento"):
        t = st.selectbox("Tipo", ["Uscita", "Entrata"])
        c = st.selectbox("Conto", df_conti['Conto'].tolist())
        v = st.number_input("Importo (€)", min_value=0.0)
        n = st.text_input("Nota")
        if st.form_submit_button("REGISTRA"):
            # Calcolo ID sicuro
            new_id = 1 if df_db.empty else df_db['ID'].max() + 1
            new_row = pd.DataFrame([[new_id, datetime.now().strftime("%Y-%m-%d"), t, c, v, n]], 
                                   columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            # Salvataggio immediato su file
            df_db = pd.concat([df_db, new_row], ignore_index=True)
            df_db.to_csv(DB_FILE, index=False)
            st.success("Dato salvato nel file locale!")
            st.rerun()

    st.dataframe(df_db.sort_values("ID", ascending=False), use_container_width=True)

with tabs[2]:
    st.subheader("Esporta Dati")
    # Trucco per non perdere i dati: scaricali ogni tanto!
    csv = df_db.to_csv(index=False).encode('utf-8')
    st.download_button("SCARICA BACKUP (CSV)", data=csv, file_name="backup_finanze.csv", mime="text/csv")
