import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import os

# --- 1. CONFIGURAZIONE AMBIENTE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

# Forza Streamlit a cercare i segreti nella cartella corretta
os.environ["STREAMLIT_CONFIG_DIR"] = "C:/Gestione_reacto/.streamlit"

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE E CARICAMENTO ---
# Specifichiamo la connessione gsheets definita nel secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Carichiamo i dati forzando il refresh (ttl=0)
        df = conn.read(worksheet="Dati", ttl=0)
        settings = conn.read(worksheet="Settings", ttl=0)
        b_df = conn.read(worksheet="Budget", ttl=0)
        
        # Pulizia e formattazione colonne
        if df.empty or 'Conto' not in df.columns:
            df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        
        df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mese_Anno'] = df['Data_dt'].dt.strftime('%Y-%m')

        if settings.empty or 'Conto' not in settings.columns:
            settings = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]})
        
        budget = float(b_df['Valore'].iloc[0]) if not b_df.empty else 1000.0
        return df, settings, budget
    except Exception as e:
        # Se c'è un errore di permessi, lo mostriamo chiaramente
        st.error(f"Errore di connessione: {e}")
        return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']), pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"]}), 1000.0

# Carichiamo i dati globali
df_db, df_settings, budget_mensile = load_data()
lista_conti = df_settings['Conto'].dropna().unique().tolist()

def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- 3. DASHBOARD SUPERIORE ---
st.title("🚀 ReactoFinance: Startup Dashboard")

mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum() if not df_db.empty else 0.0

m_cols = st.columns(len(lista_conti) + 1)
for i, nome_c in enumerate(lista_conti):
    m_cols[i].metric(nome_c, f"€ {get_saldo(nome_c):,.2f}")

colore_b = "normal" if spesa_mese <= budget_mensile else "inverse"
m_cols[-1].metric("Spesa Mese", f"€ {spesa_mese:,.2f}", f"Budget: € {budget_mensile}", delta_color=colore_b)

# --- TAB ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "🤖 AI ADVISOR", "⛏️ METALLI", "⚙️ SETUP"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Nuovo Movimento")
        with st.form("add_mov", clear_on_submit=True):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            c = st.selectbox("Conto", lista_conti)
            v = st.number_input("Importo €", min_value=0.0, step=0.01)
            n = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], columns=['ID','Data','Tipo','Conto','Importo','Nota'])
                df_final = pd.concat([df_db[['ID','Data','Tipo','Conto','Importo','Nota']], new_row])
                conn.update(worksheet="Dati", data=df_final)
                st.success("Dato salvato sul Cloud!")
                st.rerun()
    with c2:
        st.subheader("Elimina Movimento")
        del_id = st.number_input("Inserisci ID", min_value=0, step=1)
        if st.button("🗑️ ELIMINA"):
            df_cleaned = df_db[df_db['ID'] != del_id][['ID','Data','Tipo','Conto','Importo','Nota']]
            conn.update(worksheet="Dati", data=df_cleaned)
            st.rerun()
    
    st.divider()
    st.dataframe(df_db[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', title="Cash Flow Mensile"), use_container_width=True)

with tab3:
    st.info("Advisor: Il tuo capitale per la startup sta crescendo. Mantieni le uscite sotto il budget mensile.")

with tab4:
    s_m = st.selectbox("Metallo:", ["GC=F", "SI=F", "HG=F"])
    d_m = yf.download(s_m, period="1mo", progress=False)
    st.plotly_chart(px.line(d_m['Close']), use_container_width=True)

with tab5:
    st.subheader("Setup Conti")
    nc = st.text_input("Nuovo Conto")
    if st.button("AGGIUNGI"):
        new_s = pd.concat([df_settings[['Conto']], pd.DataFrame({'Conto': [nc]})], ignore_index=True)
        conn.update(worksheet="Settings", data=new_s)
        st.rerun()
