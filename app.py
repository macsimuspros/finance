import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

# CSS Originale
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE E CARICAMENTO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_data():
    # Caricamento Dati
    df = conn.read(worksheet="Dati", ttl=0)
    if df.empty:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
    df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df['Mese_Anno'] = df['Data_dt'].dt.strftime('%Y-%m')
    
    # Caricamento Settings
    settings = conn.read(worksheet="Settings", ttl=0)
    if settings.empty:
        settings = pd.DataFrame({'Conto': ["Principale"]})
        
    # Caricamento Budget
    try:
        b_df = conn.read(worksheet="Budget", ttl=0)
        budget = float(b_df['Valore'].iloc[0])
    except:
        budget = 1000.0
        
    return df, settings, budget

df_db, df_settings, budget_mensile = load_all_data()

def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- 3. DASHBOARD ---
st.title("Dashboard Finanziaria Startup")

# Calcolo Spesa Mese Corrente
mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum() if not df_db.empty else 0.0

# Metriche Superiori
m_cols = st.columns(len(df_settings) + 1)
for i, (idx, row) in enumerate(df_settings.iterrows()):
    m_cols[i].metric(row['Conto'], f"€ {get_saldo(row['Conto']):,.2f}")

colore_budget = "normal" if spesa_mese <= budget_mensile else "inverse"
m_cols[-1].metric("Spesa Mese Corrente", f"€ {spesa_mese:,.2f}", f"Budget: € {budget_mensile}", delta_color=colore_budget)

# Progress Bar Startup (Target fisso 50k come originale)
saldo_st = get_saldo("Risparmi Startup")
target = 50000.0
perc = min(max(saldo_st/target, 0.0), 1.0)
st.write(f"### 🚀 Avanzamento Obiettivo Startup: {perc*100:.1f}%")
st.progress(perc)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "🤖 AI CHAT", "⛏️ METALLI", "⚙️ SETUP"])

# --- TAB 1: GESTIONE ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        with st.form("add_mov", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Entrata", "Uscita"])
            conto = st.selectbox("Conto", df_settings['Conto'].tolist())
            val = st.number_input("Importo €", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), tipo, conto, val, nota]], 
                                       columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
                conn.update(worksheet="Dati", data=pd.concat([df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']], new_row], ignore_index=True))
                st.success("Registrato sul Cloud!")
                st.rerun()
    with c2:
        del_id = st.number_input("ID riga da eliminare", min_value=0, step=1)
        if st.button("🗑️ RIMUOVI"):
            conn.update(worksheet="Dati", data=df_db[df_db['ID'] != del_id][['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']])
            st.rerun()

    st.markdown("---")
    st.subheader("🔍 Filtri di Ricerca")
    f1, f2, f3 = st.columns([2, 1, 1])
    s_txt = f1.text_input("Cerca nelle note...")
    s_tipo = f2.selectbox("Tipo", ["Tutti", "Solo Entrate", "Solo Uscite"])
    s_conto = f3.selectbox("Conto", ["Tutti"] + df_settings['Conto'].tolist())
    
    df_f = df_db.copy()
    if s_txt: df_f = df_f[df_f['Nota'].str.contains(s_txt, case=False, na=False)]
    if s_tipo == "Solo Entrate": df_f = df_f[df_f['Tipo'] == "Entrata"]
    elif s_tipo == "Solo Uscite": df_f = df_f[df_f['Tipo'] == "Uscita"]
    if s_conto != "Tutti": df_f = df_f[df_f['Conto'] == s_conto]
    
    st.dataframe(df_f[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)
    
    if not df_db.empty:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']].to_excel(writer, index=False)
        st.download_button("📥 SCARICA EXCEL", data=buf.getvalue(), file_name="Report_Reacto.xlsx")

# --- TAB 2: ANALISI ---
with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', title="Trend Mensile"), use_container_width=True)
        
        ca, cb = st.columns(2)
        with ca:
            st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Entrata'], values='Importo', names='Conto', title="Origine Entrate", hole=0.4), use_container_width=True)
        with cb:
            st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Uscita'], values='Importo', names='Conto', title="Destinazione Uscite", hole=0.4), use_container_width=True)

# --- TAB 4: METALLI ---
with tab4:
    mets = {"Oro": "GC=F", "Argento": "SI=F", "Rame": "HG=F", "Platino": "PL=F"}
    s_m = st.selectbox("Asset:", list(mets.keys()))
    d_m = yf.download(mets[s_m], period="1mo", progress=False)
    st.plotly_chart(px.line(d_m['Close'], title=f"Prezzo {s_m}"), use_container_width=True)

# --- TAB 5: SETUP ---
with tab5:
    # Gestione Budget
    nb = st.number_input("Nuovo Budget Mensile (€)", value=budget_mensile)
    if st.button("AGGIORNA BUDGET"):
        conn.update(worksheet="Budget", data=pd.DataFrame({'Valore': [nb]}))
        st.rerun()

    st.markdown("---")
    # Gestione Conti
    nc = st.text_input("Aggiungi Conto")
    if st.button("SALVA CONTO"):
        new_s = pd.concat([df_settings[['Conto']], pd.DataFrame({'Conto': [nc]})], ignore_index=True)
        conn.update(worksheet="Settings", data=new_s)
        st.rerun()
    
    ec = st.selectbox("Elimina Conto", df_settings['Conto'].tolist())
    if st.button("ELIMINA SELEZIONATO"):
        conn.update(worksheet="Settings", data=df_settings[df_settings['Conto'] != ec][['Conto']])
        st.rerun()
