import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

# CSS Personalizzato (Originale)
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    try:
        # Caricamento Dati
        df = conn.read(worksheet="Dati", ttl=0)
        if df.empty or 'Conto' not in df.columns:
            df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        
        # Pulizia dati per calcoli
        df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mese_Anno'] = df['Data_dt'].dt.strftime('%Y-%m')
        
        # Caricamento Settings (Conti)
        settings = conn.read(worksheet="Settings", ttl=0)
        if settings.empty or 'Conto' not in settings.columns:
            settings = pd.DataFrame({'Conto': ["Principale"]})
            
        # Caricamento Budget
        b_df = conn.read(worksheet="Budget", ttl=0)
        budget = float(b_df['Valore'].iloc[0]) if not b_df.empty else 1000.0
        
        return df, settings, budget
    except:
        return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']), pd.DataFrame({'Conto': ["Principale"]}), 1000.0

df_db, df_settings, budget_mensile = load_all_data()

def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- DASHBOARD ---
st.title("🚀 Dashboard Finanziaria Startup")

# Calcolo Spesa Mese
mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum() if not df_db.empty else 0.0

# Metriche Superiori (Risolve il KeyError)
lista_conti = df_settings['Conto'].dropna().tolist()
m_cols = st.columns(len(lista_conti) + 1)
for i, nome_conto in enumerate(lista_conti):
    m_cols[i].metric(nome_conto, f"€ {get_saldo(nome_conto):,.2f}")

# Metrica Budget
colore_budget = "normal" if spesa_mese <= budget_mensile else "inverse"
m_cols[-1].metric("Spesa Mese", f"€ {spesa_mese:,.2f}", f"Target: € {budget_mensile}", delta_color=colore_budget)

# Progress Bar (Obiettivo 50k)
saldo_st = get_saldo("Risparmi Startup")
target = 50000.0
perc = min(max(saldo_st/target, 0.0), 1.0)
st.write(f"### 📈 Avanzamento Obiettivo: {perc*100:.1f}%")
st.progress(perc)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📉 ANALISI", "🤖 AI CHAT", "⛏️ METALLI", "⚙️ SETUP"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        with st.form("add_mov", clear_on_submit=True):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            c = st.selectbox("Conto", lista_conti)
            v = st.number_input("Importo €", min_value=0.0)
            n = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
                conn.update(worksheet="Dati", data=pd.concat([df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']], new_row]))
                st.rerun()
    with c2:
        del_id = st.number_input("ID da rimuovere", min_value=0, step=1)
        if st.button("🗑️ ELIMINA"):
            conn.update(worksheet="Dati", data=df_db[df_db['ID'] != del_id][['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']])
            st.rerun()
    
    st.subheader("Storico Movimenti")
    st.dataframe(df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']].sort_values("ID", ascending=False), use_container_width=True)

with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', title="Trend Mensile"), use_container_width=True)
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Entrata'], values='Importo', names='Conto', title="Entrate per Conto"), use_container_width=True)
        with cb: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Uscita'], values='Importo', names='Conto', title="Uscite per Conto"), use_container_width=True)

with tab4:
    asset = st.selectbox("Asset:", ["GC=F", "SI=F", "HG=F", "PL=F"], format_func=lambda x: "Oro" if x=="GC=F" else "Argento")
    data_m = yf.download(asset, period="1mo", progress=False)
    st.plotly_chart(px.line(data_m['Close'], title=f"Prezzo {asset}"), use_container_width=True)

with tab5:
    nb = st.number_input("Imposta Budget Mensile (€)", value=budget_mensile)
    if st.button("SALVA BUDGET"):
        conn.update(worksheet="Budget", data=pd.DataFrame({'Valore': [nb]}))
        st.rerun()
