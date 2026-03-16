import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATI CLOUD ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_sheet_data(sheet_name, default_cols=None):
    try:
        return conn.read(worksheet=sheet_name, ttl=0)
    except:
        return pd.DataFrame(columns=default_cols) if default_cols else pd.DataFrame()

# Caricamento tabelle dal Cloud
df_db = load_sheet_data("Dati", ['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
df_settings = load_sheet_data("Settings", ['Conto', 'Target'])
df_budget = load_sheet_data("Budget", ['Valore'])

# Gestione valori di default se i fogli sono vuoti
if df_settings.empty:
    df_settings = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup"], 'Target': [0.0, 50000.0]})
if df_budget.empty:
    budget_mensile = 1000.0
else:
    budget_mensile = float(df_budget['Valore'].iloc[0])

# Pre-processing Dati
if not df_db.empty:
    df_db['Importo'] = pd.to_numeric(df_db['Importo'], errors='coerce').fillna(0.0)
    df_db['Data_dt'] = pd.to_datetime(df_db['Data'], format='%d/%m/%Y', errors='coerce')
    df_db['Mese_Anno'] = df_db['Data_dt'].dt.strftime('%Y-%m')

def get_saldo(nome):
    if df_db.empty: return 0.0
    e = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Entrata')]['Importo'].sum()
    u = df_db[(df_db['Conto'] == nome) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()
    return float(e - u)

# --- 3. DASHBOARD ---
st.title("Dashboard Finanziaria Startup")

# Calcolo Spesa Mese Corrente
mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = 0.0
if not df_db.empty:
    spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum()

# Metriche
m_cols = st.columns(len(df_settings) + 1)
for i, row in df_settings.iterrows():
    m_cols[i].metric(row['Conto'], f"€ {get_saldo(row['Conto']):,.2f}")

colore_budget = "normal" if spesa_mese <= budget_mensile else "inverse"
m_cols[-1].metric("Spesa Mese Corrente", f"€ {spesa_mese:,.2f}", f"Budget: € {budget_mensile}", delta_color=colore_budget)

# Progress Bar Startup
saldo_st = get_saldo("Risparmi Startup")
target_st = 50000.0
perc = min(max(saldo_st/target_st, 0.0), 1.0)
st.write(f"### 🚀 Avanzamento Obiettivo: {perc*100:.1f}%")
st.progress(perc)

if spesa_mese > budget_mensile:
    st.warning(f"⚠️ Attenzione: Hai superato il budget mensile di € {spesa_mese - budget_mensile:,.2f}!")

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
                df_updated = pd.concat([df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']], new_row], ignore_index=True)
                conn.update(worksheet="Dati", data=df_updated)
                st.rerun()
    with c2:
        del_id = st.number_input("ID riga da eliminare", min_value=0, step=1)
        if st.button("🗑️ RIMUOVI"):
            df_updated = df_db[df_db['ID'] != del_id][['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']]
            conn.update(worksheet="Dati", data=df_updated)
            st.rerun()

    st.markdown("---")
    st.dataframe(df_db[['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: ANALISI ---
with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        fig_bar = px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', color_discrete_map={'Entrata': '#238636', 'Uscita': '#da3633'})
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: AI CHAT ---
with tab3:
    st.subheader("🤖 AI Startup Advisor")
    if p := st.chat_input("Chiedi un consiglio..."):
        st.write(f"Analisi per Ingegneria Chimica: Con un saldo startup di € {saldo_st:,.2f}, il tuo risparmio è al {perc*100:.1f}% del target.")

# --- TAB 4: METALLI ---
with tab4:
    mets = {"Oro": "GC=F", "Argento": "SI=F", "Rame": "HG=F", "Palladio": "PA=F", "Nichel": "NI=F"}
    s_m = st.selectbox("Asset:", list(mets.keys()))
    d_m = yf.download(mets[s_m], period="1mo", progress=False)
    st.plotly_chart(px.line(d_m['Close'], title=f"Prezzo {s_m}"), use_container_width=True)

# --- TAB 5: SETUP ---
with tab5:
    # Aggiorna Budget
    nuovo_b = st.number_input("Nuovo Budget Mensile (€)", value=budget_mensile)
    if st.button("SALVA BUDGET"):
        df_b_new = pd.DataFrame({'Valore': [nuovo_b]})
        conn.update(worksheet="Budget", data=df_b_new)
        st.rerun()
    
    # Aggiungi Conto
    n_c = st.text_input("Nome nuovo conto")
    if st.button("AGGIUNGI CONTO"):
        new_c_df = pd.concat([df_settings[['Conto', 'Target']], pd.DataFrame({'Conto': [n_c], 'Target': [0.0]})], ignore_index=True)
        conn.update(worksheet="Settings", data=new_c_df)
        st.rerun()
