import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURAZIONE AMBIENTE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

# Forza Streamlit a cercare i segreti nella cartella locale del tuo PC
os.environ["STREAMLIT_CONFIG_DIR"] = "C:/Gestione_reacto/.streamlit"

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE DATI (GOOGLE SHEETS) ---
def load_data():
    try:
        # Utilizza la connessione definita nel secrets.toml
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Lettura delle tre schede principali
        df = conn.read(worksheet="Dati", ttl=0)
        settings = conn.read(worksheet="Settings", ttl=0)
        b_df = conn.read(worksheet="Budget", ttl=0)
        
        # Inizializzazione se vuoti
        if df.empty:
            df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        
        # Formattazione dati
        df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mese_Anno'] = df['Data_dt'].dt.strftime('%Y-%m')

        if settings.empty:
            settings = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]})
            
        budget = float(b_df['Valore'].iloc[0]) if not b_df.empty else 1000.0
        
        return conn, df, settings, budget
    except Exception as e:
        st.error(f"❌ Errore di connessione al Cloud: {e}")
        st.info("Controlla che il file secrets.toml sia formattato correttamente e che il link dello spreadsheet sia giusto.")
        st.stop()

conn, df_db, df_settings, budget_mensile = load_data()
lista_conti = df_settings['Conto'].dropna().unique().tolist()

# Funzione per calcolare il saldo in tempo reale
def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- 3. INTERFACCIA PRINCIPALE ---
st.title("🚀 ReactoFinance: Startup Dashboard")

# Metriche in alto
mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum() if not df_db.empty else 0.0

m_cols = st.columns(len(lista_conti) + 1)
for i, nome_c in enumerate(lista_conti):
    m_cols[i].metric(nome_c, f"€ {get_saldo(nome_c):,.2f}")

colore_budget = "normal" if spesa_mese <= budget_mensile else "inverse"
m_cols[-1].metric("Spesa Mese", f"€ {spesa_mese:,.2f}", f"Budget: € {budget_mensile}", delta_color=colore_budget)

# Tab di navigazione
tab1, tab2, tab3, tab4 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "⛏️ METALLI", "⚙️ SETUP"])

# --- TAB 1: GESTIONE ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registra Movimento")
        with st.form("add_mov", clear_on_submit=True):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            c = st.selectbox("Conto", lista_conti)
            v = st.number_input("Importo €", min_value=0.0, step=0.01)
            n = st.text_input("Nota")
            if st.form_submit_button("SALVA NEL CLOUD"):
                nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], 
                                       columns=['ID','Data','Tipo','Conto','Importo','Nota'])
                df_updated = pd.concat([df_db[['ID','Data','Tipo','Conto','Importo','Nota']], new_row])
                conn.update(worksheet="Dati", data=df_updated)
                st.success("Dato sincronizzato!")
                st.rerun()
    with c2:
        st.subheader("Elimina")
        del_id = st.number_input("ID Movimento", min_value=0, step=1)
        if st.button("🗑️ RIMUOVI"):
            df_cleaned = df_db[df_db['ID'] != del_id][['ID','Data','Tipo','Conto','Importo','Nota']]
            conn.update(worksheet="Dati", data=df_cleaned)
            st.rerun()
    
    st.divider()
    st.dataframe(df_db[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), 
                 use_container_width=True, hide_index=True)

# --- TAB 2: ANALISI ---
with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', title="Cash Flow Mensile"), use_container_width=True)
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Entrata'], values='Importo', names='Conto', title="Distribuzione Entrate"), use_container_width=True)
        with cb: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Uscita'], values='Importo', names='Conto', title="Distribuzione Uscite"), use_container_width=True)

# --- TAB 3: METALLI ---
with tab4:
    st.subheader("Monitoraggio Materie Prime")
    metallo = st.selectbox("Seleziona:", ["Oro (GC=F)", "Argento (SI=F)", "Rame (HG=F)"])
    ticker = metallo.split("(")[1].replace(")", "")
    dati_metallo = yf.download(ticker, period="1mo", progress=False)
    st.plotly_chart(px.line(dati_metallo['Close'], title=f"Prezzo {metallo} - Ultimi 30 giorni"), use_container_width=True)

# --- TAB 4: SETUP ---
with tab5:
    st.subheader("Impostazioni Budget e Conti")
    new_budget = st.number_input("Modifica Budget Mensile (€)", value=budget_mensile)
    if st.button("AGGIORNA BUDGET"):
        conn.update(worksheet="Budget", data=pd.DataFrame({'Valore': [new_budget]}))
        st.success("Budget aggiornato!")
        st.rerun()
