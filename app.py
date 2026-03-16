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
        
        # Pulizia Dati
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
st.write(f"### 🎯 Target Startup: {perc*100:.1f}%")
st.progress(perc)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "🤖 AI CHAT", "⛏️ METALLI", "⚙️ SETUP"])

# --- TAB 1: GESTIONE (FILTRI E MODIFICA) ---
with tab1:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Nuovo Movimento")
        with st.form("add", clear_on_submit=True):
            t = st.selectbox("Tipo", ["Entrata", "Uscita"])
            c = st.selectbox("Conto", lista_conti)
            v = st.number_input("Importo €", min_value=0.0)
            n = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                nid = 1 if df_db.empty else int(df_db['ID'].max() + 1)
                new_row = pd.DataFrame([[nid, datetime.now().strftime("%d/%m/%Y"), t, c, v, n]], columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
                conn.update(worksheet="Dati", data=pd.concat([df_db[['ID','Data','Tipo','Conto','Importo','Nota']], new_row]))
                st.rerun()
    with c2:
        st.subheader("Elimina Riga")
        del_id = st.number_input("Inserisci ID da eliminare", min_value=0, step=1)
        if st.button("🗑️ CONFERMA ELIMINAZIONE"):
            conn.update(worksheet="Dati", data=df_db[df_db['ID'] != del_id][['ID','Data','Tipo','Conto','Importo','Nota']])
            st.rerun()

    st.divider()
    st.subheader("🔍 Filtri Avanzati")
    f_txt, f_t, f_c = st.columns([2,1,1])
    txt = f_txt.text_input("Cerca nelle note...")
    tipo_s = f_t.selectbox("Tipo", ["Tutti", "Entrata", "Uscita"])
    conto_s = f_c.selectbox("Conto", ["Tutti"] + lista_conti)
    
    df_f = df_db.copy()
    if txt: df_f = df_f[df_f['Nota'].str.contains(txt, case=False, na=False)]
    if tipo_s != "Tutti": df_f = df_f[df_f['Tipo'] == tipo_s]
    if conto_s != "Tutti": df_f = df_f[df_f['Conto'] == conto_s]
    
    st.dataframe(df_f[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 3: AI CHAT ---
with tab3:
    st.subheader("🤖 AI Startup Advisor")
    st.info("L'AI analizza il tuo saldo attuale per darti consigli sulla startup.")
    user_q = st.chat_input("Chiedi all'AI...")
    if user_q:
        st.write(f"**Tu:** {user_q}")
        st.write(f"**AI:** Basandomi sul tuo saldo di € {saldo_st:,.2f}, ti consiglio di monitorare bene le uscite di questo mese (€ {spesa_mese:,.2f}) per non rallentare l'obiettivo dei 50k.")

# --- TAB 4: METALLI (COMPLETI) ---
with tab4:
    mets = {
        "Oro": "GC=F", "Argento": "SI=F", "Rame": "HG=F", 
        "Platino": "PL=F", "Palladio": "PA=F", "Nichel": "NI=F", 
        "Alluminio": "ALI=F", "Zinco": "ZNC=F"
    }
    s_m = st.selectbox("Asset:", list(mets.keys()))
    d_m = yf.download(mets[s_m], period="1mo", progress=False)
    if not d_m.empty:
        st.plotly_chart(px.line(d_m['Close'], title=f"Trend {s_m} (30gg)"), use_container_width=True)

# --- TAB 5: SETUP (CONTI E BUDGET) ---
with tab5:
    st.subheader("Impostazioni Sistema")
    col_b, col_c = st.columns(2)
    with col_b:
        new_b = st.number_input("Modifica Budget Mensile (€)", value=budget_mensile)
        if st.button("AGGIORNA BUDGET"):
            conn.update(worksheet="Budget", data=pd.DataFrame({'Valore': [new_b]}))
            st.rerun()
    with col_c:
        n_c = st.text_input("Aggiungi nuovo conto")
        if st.button("SALVA CONTO"):
            new_s = pd.concat([df_settings[['Conto']], pd.DataFrame({'Conto': [n_c]})], ignore_index=True)
            conn.update(worksheet="Settings", data=new_s)
            st.rerun()
        
        st.divider()
        e_c = st.selectbox("Elimina un conto", lista_conti)
        if st.button("🗑️ ELIMINA CONTO"):
            conn.update(worksheet="Settings", data=df_settings[df_settings['Conto'] != e_c][['Conto']])
            st.rerun()
