import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

# Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Lettura fogli
        d_db = conn.read(worksheet="Dati", ttl=0)
        d_set = conn.read(worksheet="Settings", ttl=0)
        
        # Se il foglio Dati è vuoto, crea struttura
        if d_db.empty:
            d_db = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            
        # Se il foglio Settings è vuoto o manca la colonna, crea default
        if d_set.empty or 'Conto' not in d_set.columns:
            d_set = pd.DataFrame({'Conto': ['Principale']})
            
        return d_db, d_set
    except Exception:
        return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']), \
               pd.DataFrame({'Conto': ['Principale']})

df_db, df_settings = load_data()
lista_conti = df_settings['Conto'].dropna().unique().tolist()

st.title("🚀 ReactoFinance: Startup Dashboard")

# --- SEZIONE SALDI ---
st.subheader("Stato Conti")
if lista_conti:
    cols = st.columns(len(lista_conti))
    for i, c_name in enumerate(lista_conti):
        if not df_db.empty and 'Conto' in df_db.columns:
            entrate = df_db[(df_db['Conto'] == c_name) & (df_db['Tipo'] == 'Entrata')]['Importo'].astype(float).sum()
            uscite = df_db[(df_db['Conto'] == c_name) & (df_db['Tipo'] == 'Uscita')]['Importo'].astype(float).sum()
            saldo = entrate - uscite
        else:
            saldo = 0.0
        cols[i].metric(c_name, f"{saldo:.2f} €")

st.divider()

# --- TAB ---
t1, t2, t3 = st.tabs(["📊 MOVIMENTI", "📈 METALLI", "⚙️ SETUP"])

with t1:
    c_dx, c_sx = st.columns([2, 1])
    with c_dx:
        search = st.text_input("🔍 Cerca nota o conto...")
        if not df_db.empty:
            # Filtro ricerca
            mask = df_db.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            st.dataframe(df_db[mask].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nessun dato presente.")

    with c_sx:
        st.subheader("Nuova Registrazione")
        with st.form("form_new", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Entrata", "Uscita"])
            conto_sel = st.selectbox("Conto", lista_conti)
            valore = st.number_input("Importo €", min_value=0.0, step=0.01)
            nota = st.text_input("Descrizione")
            if st.form_submit_button("REGISTRA"):
                # Calcolo nuovo ID
                new_id = int(df_db['ID'].max() + 1) if not df_db.empty else 1
                # Creazione riga
                new_row = pd.DataFrame([[new_id, datetime.now().strftime("%d/%m/%Y"), tipo, conto_sel, valore, nota]], 
                                       columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
                # Update Cloud
                df_final = pd.concat([df_db, new_row], ignore_index=True)
                conn.update(worksheet="Dati", data=df_final)
                st.success("Sincronizzato!")
                st.rerun()

with t2:
    st.subheader("Analisi Oro e Argento")
    m_sel = st.selectbox("Seleziona Asset", ["GC=F", "SI=F", "HG=F"], format_func=lambda x: "Oro" if x=="GC=F" else ("Argento" if x=="SI=F" else "Rame"))
    data_yf = yf.download(m_sel, period="1mo")
    if not data_yf.empty:
        st.line_chart(data_yf['Close'])

with t3:
    st.subheader("Gestione Startup")
    with st.expander("Aggiungi nuovo conto"):
        n_c = st.text_input("Nome conto (es. Wallet Crypto, Revolut)")
        if st.button("Salva"):
            new_s = pd.concat([df_settings, pd.DataFrame({'Conto': [n_c]})], ignore_index=True)
            conn.update(worksheet="Settings", data=new_s)
            st.rerun()
