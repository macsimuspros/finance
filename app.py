import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE E CARICAMENTO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Dati", ttl=0)
        settings = conn.read(worksheet="Settings", ttl=0)
        b_df = conn.read(worksheet="Budget", ttl=0)
        
        if df.empty or 'Conto' not in df.columns:
            df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        
        df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mese_Anno'] = df['Data_dt'].dt.strftime('%Y-%m')

        if settings.empty or 'Conto' not in settings.columns:
            settings = pd.DataFrame({'Conto': ["Principale"]})
        
        budget = float(b_df['Valore'].iloc[0]) if not b_df.empty else 1000.0
        return df, settings, budget
    except:
        return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']), pd.DataFrame({'Conto': ["Principale"]}), 1000.0

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

# Progress Bar Startup
saldo_st = get_saldo("Risparmi Startup")
target_st = 50000.0
perc = min(max(saldo_st/target_st, 0.0), 1.0)
st.write(f"### 🎯 Avanzamento Obiettivo Startup: {perc*100:.1f}%")
st.progress(perc)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "🤖 AI CHAT", "⛏️ METALLI", "⚙️ SETUP"])

# --- TAB 1: GESTIONE ---
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
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], columns=['ID','Data','Tipo','Conto','Importo','Nota'])
                conn.update(worksheet="Dati", data=pd.concat([df_db[['ID','Data','Tipo','Conto','Importo','Nota']], new_row]))
                st.rerun()
    with c2:
        del_id = st.number_input("ID da eliminare", min_value=0, step=1)
        if st.button("🗑️ ELIMINA"):
            conn.update(worksheet="Dati", data=df_db[df_db['ID'] != del_id][['ID','Data','Tipo','Conto','Importo','Nota']])
            st.rerun()
    
    st.divider()
    txt = st.text_input("🔍 Filtra per nota...")
    df_f = df_db[df_db['Nota'].str.contains(txt, case=False, na=False)] if txt else df_db
    st.dataframe(df_f[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: ANALISI ---
with tab2:
    if not df_db.empty:
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        st.plotly_chart(px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', title="Trend Mensile"), use_container_width=True)
        
        ca, cb = st.columns(2)
        with ca: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Entrata'], values='Importo', names='Conto', title="Entrate", hole=0.4), use_container_width=True)
        with cb: st.plotly_chart(px.pie(df_db[df_db['Tipo']=='Uscita'], values='Importo', names='Conto', title="Uscite", hole=0.4), use_container_width=True)

# --- TAB 3: AI CHAT ---
with tab3:
    st.subheader("🤖 AI Startup Advisor")
    msg = st.chat_input("Chiedi un consiglio finanziario...")
    if msg:
        st.write(f"**Tu:** {msg}")
        # Logica Advisor basata sui dati reali
        budget_rimasto = budget_mensile - spesa_mese
        consiglio = ""
        if spesa_mese > budget_mensile:
            consiglio = f"⚠️ Sei fuori budget di €{abs(budget_rimasto):,.2f}! Per la tua startup, dovresti tagliare le spese non essenziali questo mese."
        elif saldo_st < 10000:
            consiglio = "🌱 Sei nella fase di accumulo iniziale. Ogni euro risparmiato oggi è capitale per la tua futura azienda chimica."
        else:
            consiglio = f"🚀 Ottimo lavoro! Hai già accumulato €{saldo_st:,.2f}. Continua così per raggiungere il target di 50k."
        
        st.write(f"**AI Advisor:** {consiglio}")

# --- TAB 4: METALLI ---
with tab4:
    mets = {"Oro": "GC=F", "Argento": "SI=F", "Rame": "HG=F", "Platino": "PL=F", "Palladio": "PA=F", "Nichel": "NI=F", "Alluminio": "ALI=F"}
    s_m = st.selectbox("Seleziona Metallo:", list(mets.keys()))
    d_m = yf.download(mets[s_m], period="1mo", progress=False)
    st.plotly_chart(px.line(d_m['Close'], title=f"Prezzo {s_m} (Ultimi 30gg)"), use_container_width=True)

# --- TAB 5: SETUP (BUDGET E CONTI) ---
with tab5:
    st.subheader("Impostazioni")
    # GESTIONE BUDGET
    st.write("### 💰 Budget Mensile")
    nb = st.number_input("Imposta tetto massimo spese (€)", value=budget_mensile)
    if st.button("AGGIORNA BUDGET"):
        conn.update(worksheet="Budget", data=pd.DataFrame({'Valore': [nb]}))
        st.success("Budget aggiornato con successo!")
        st.rerun()

    st.divider()
    # GESTIONE CONTI
    st.write("### 🏦 Gestione Conti")
    nc = st.text_input("Aggiungi nuovo conto")
    if st.button("SALVA CONTO"):
        new_s = pd.concat([df_settings[['Conto']], pd.DataFrame({'Conto': [nc]})], ignore_index=True)
        conn.update(worksheet="Settings", data=new_s)
        st.rerun()
    
    ec = st.selectbox("Elimina un conto", lista_conti)
    if st.button("ELIMINA SELEZIONATO"):
        conn.update(worksheet="Settings", data=df_settings[df_settings['Conto'] != ec][['Conto']])
        st.rerun()
