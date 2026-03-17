import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURAZIONE AMBIENTE (FORZATA) ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

# Indichiamo a Python dove cercare la cartella .streamlit
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["STREAMLIT_CONFIG_DIR"] = os.path.join(current_dir, ".streamlit")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE ---
try:
    # Connessione forzata usando i segreti caricati
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Specifichiamo esplicitamente il link se Streamlit non lo legge dal TOML
    # Sostituisci il link qui sotto se diverso da quello in foto
    url = "https://docs.google.com/spreadsheets/d/1CjFG26e7yf-yRYXlfwmRsyuu6dfyn7LUV1AfXpVGNE8/edit#gid=0"
    
    df_db = conn.read(spreadsheet=url, worksheet="Dati", ttl=0)
    df_settings = conn.read(spreadsheet=url, worksheet="Settings", ttl=0)
    b_df = conn.read(spreadsheet=url, worksheet="Budget", ttl=0)
    
    # Pulizia dati
    df_db['Importo'] = pd.to_numeric(df_db['Importo'], errors='coerce').fillna(0.0)
    df_db['Data_dt'] = pd.to_datetime(df_db['Data'], format='%d/%m/%Y', errors='coerce')
    df_db['Mese_Anno'] = df_db['Data_dt'].dt.strftime('%Y-%m')
    
    lista_conti = df_settings['Conto'].dropna().unique().tolist() if not df_settings.empty else ["Principale"]
    budget_mensile = float(b_df['Valore'].iloc[0]) if not b_df.empty else 1000.0

except Exception as e:
    st.error(f"⚠️ Errore critico: {e}")
    st.stop()

# --- 3. LOGICA SALDO ---
def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- 4. DASHBOARD ---
st.title("🚀 ReactoFinance: Startup Dashboard")

cols = st.columns(len(lista_conti) + 1)
for i, nome_c in enumerate(lista_conti):
    cols[i].metric(nome_c, f"€ {get_saldo(nome_c):,.2f}")

# --- TAB ---
tab1, tab2, tab3 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "⚙️ SETUP"])

with tab1:
    with st.form("add_mov", clear_on_submit=True):
        col1, col2 = st.columns(2)
        t = col1.selectbox("Tipo", ["Entrata", "Uscita"])
        c = col1.selectbox("Conto", lista_conti)
        v = col2.number_input("Importo €", min_value=0.0, step=0.01)
        n = col2.text_input("Nota")
        if st.form_submit_button("REGISTRA MOVIMENTO"):
            nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
            new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], 
                                   columns=['ID','Data','Tipo','Conto','Importo','Nota'])
            df_final = pd.concat([df_db[['ID','Data','Tipo','Conto','Importo','Nota']], new_row])
            conn.update(spreadsheet=url, worksheet="Dati", data=df_final)
            st.success("Sincronizzato col Cloud!")
            st.rerun()
    
    st.divider()
    st.dataframe(df_db[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group'), use_container_width=True)
