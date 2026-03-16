import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import io

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    [data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .stProgress > div > div > div > div { background-color: #238636 !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(worksheet="Dati", ttl=0)
        settings = conn.read(worksheet="Settings", ttl=0)
        b_df = conn.read(worksheet="Budget", ttl=0)
        
        if df.empty or 'Conto' not in df.columns:
            df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        
        df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
        # Gestione date per l'analisi
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

st.title("🚀 ReactoFinance: Startup Dashboard")

# --- DASHBOARD SUPERIORE ---
mese_attuale = datetime.now().strftime('%Y-%m')
spesa_mese = df_db[(df_db['Mese_Anno'] == mese_attuale) & (df_db['Tipo'] == 'Uscita')]['Importo'].sum() if not df_db.empty else 0.0

m_cols = st.columns(len(lista_conti) + 1)
for i, nome_c in enumerate(lista_conti):
    m_cols[i].metric(nome_c, f"€ {get_saldo(nome_c):,.2f}")

m_cols[-1].metric("Spesa Mese", f"€ {spesa_mese:,.2f}", f"Budget: € {budget_mensile}")

# --- BARRA TARGET STARTUP ---
# Cerchiamo il saldo del conto specifico per la startup
nome_target = "Risparmi Startup" 
saldo_st = get_saldo(nome_target)
target_st = 50000.0
perc = min(max(saldo_st/target_st, 0.0), 1.0)

st.write(f"### 🎯 Avanzamento Obiettivo Startup ({nome_target}): {perc*100:.1f}%")
st.progress(perc)
if nome_target not in lista_conti:
    st.info(f"💡 Suggerimento: Aggiungi un conto chiamato '{nome_target}' nella tab SETUP per attivare il calcolo automatico.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 GESTIONE", "📈 ANALISI", "🤖 AI CHAT", "⛏️ METALLI", "⚙️ SETUP"])

with tab1:
    # (Codice gestione movimenti, filtri e cancellazione riga come prima...)
    c1, c2 = st.columns(2)
    with c1:
        with st.form("add"):
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

    st.subheader("🔍 Filtri Ricerca")
    txt = st.text_input("Cerca nelle note...")
    df_f = df_db[df_db['Nota'].str.contains(txt, case=False, na=False)] if txt else df_db
    st.dataframe(df_f[['ID','Data','Tipo','Conto','Importo','Nota']].sort_values("ID", ascending=False), use_container_width=True)

with tab2:
    st.subheader("📈 Analisi Finanziaria")
    if not df_db.empty:
        # 1. Grafico Trend
        df_trend = df_db.groupby(['Mese_Anno', 'Tipo'])['Importo'].sum().reset_index()
        fig_trend = px.bar(df_trend, x='Mese_Anno', y='Importo', color='Tipo', barmode='group', 
                           color_discrete_map={'Entrata': '#238636', 'Uscita': '#da3633'}, title="Entrate vs Uscite")
        st.plotly_chart(fig_trend, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            # 2. Torta Entrate
            df_e = df_db[df_db['Tipo'] == 'Entrata']
            if not df_e.empty:
                st.plotly_chart(px.pie(df_e, values='Importo', names='Conto', title="Distribuzione Entrate", hole=0.4), use_container_width=True)
        with col_b:
            # 3. Torta Uscite
            df_u = df_db[df_db['Tipo'] == 'Uscita']
            if not df_u.empty:
                st.plotly_chart(px.pie(df_u, values='Importo', names='Conto', title="Distribuzione Uscite", hole=0.4), use_container_width=True)
    else:
        st.info("Nessun dato disponibile per l'analisi.")

with tab3:
    st.subheader("🤖 AI Startup Advisor")
    st.write(f"Saldo attuale Startup: € {saldo_st:,.2f}")
    if st.button("Genera consiglio"):
        if saldo_st < 5000: st.write("Consiglio: Sei nelle prime fasi. Concentrati sul ridurre le uscite fisse.")
        else: st.write("Consiglio: Ottimo andamento. Valuta se parte del capitale può essere investita in asset a bassa volatilità.")

with tab4:
    # Metalli come prima...
    mets = {"Oro": "GC=F", "Argento": "SI=F", "Rame": "HG=F", "Platino": "PL=F", "Palladio": "PA=F", "Nichel": "NI=F", "Alluminio": "ALI=F"}
    s_m = st.selectbox("Asset:", list(mets.keys()))
    d_m = yf.download(mets[s_m], period="1mo", progress=False)
    st.plotly_chart(px.line(d_m['Close'], title=f"Trend {s_m}"), use_container_width=True)

with tab5:
    st.subheader("Configurazione")
    # Aggiungi Conto
    nuovo_c = st.text_input("Aggiungi nuovo conto")
    if st.button("SALVA CONTO"):
        new_s = pd.concat([df_settings[['Conto']], pd.DataFrame({'Conto': [nuovo_c]})], ignore_index=True)
        conn.update(worksheet="Settings", data=new_s)
        st.rerun()
    
    st.divider()
    # Elimina Conto
    e_c = st.selectbox("Elimina un conto", lista_conti)
    if st.button("ELIMINA CONTO"):
        conn.update(worksheet="Settings", data=df_settings[df_settings['Conto'] != e_c][['Conto']])
        st.rerun()
