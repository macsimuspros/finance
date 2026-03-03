import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="PocketFinance AI v2", layout="wide", initial_sidebar_state="collapsed")

# File per salvare i dati (Database locale)
DB_FILE = "database_finanze.csv"

# --- STILE ESTETICO (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { border-radius: 10px; background-color: #2e7bcf; color: white; width: 100%; }
    [data-testid="stMetricValue"] { color: #00FFCC; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0px 0px; padding: 10px; background-color: #1e2227; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI CUORE ---
def inizializza_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=['Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)

def salva_movimento(tipo, conto, importo, nota):
    df = pd.read_csv(DB_FILE)
    nuova_riga = {
        'Data': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'Tipo': tipo,
        'Conto': conto,
        'Importo': importo,
        'Nota': nota
    }
    df = pd.concat([df, pd.DataFrame([nuova_riga])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d")
        return data['Close']
    except:
        return None

# Inizializziamo il database all'avvio
inizializza_db()

# --- INTERFACCIA ---
st.title("💰 PocketFinance AI")
st.caption(f"Monitoraggio per Futuro Ingegnere Chimico | Data: {datetime.now().strftime('%d/%m/%Y')}")

tabs = st.tabs(["➕ Inserisci", "🔍 Cerca & Filtra", "📊 Statistiche", "⛏️ Metalli"])

# --- TAB 1: INSERIMENTO ---
with tabs[0]:
    with st.form("form_inserimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tipo = col1.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = col2.selectbox("Conto", ["Principale", "Risparmi Startup", "Investimenti", "Emergenza"])
        importo = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        nota = st.text_input("Commento (es. Libri, Rame, Pranzo)")
        
        if st.form_submit_button("REGISTRA MOVIMENTO"):
            if importo > 0:
                salva_movimento(tipo, conto, importo, nota)
                st.success(f"Registrato: {importo}€ in {conto}")
            else:
                st.error("Inserisci un importo valido!")

# --- TAB 2: RICERCA E TABELLA ---
with tabs[1]:
    st.subheader("Storico Operazioni")
    df = pd.read_csv(DB_FILE)
    
    if not df.empty:
        col_s1, col_s2 = st.columns([2, 1])
        search = col_s1.text_input("Cerca nelle note (es: 'chimica')")
        filtro_tipo = col_s2.multiselect("Filtra Tipo", df['Tipo'].unique())
        
        # Logica di filtro
        df_filtrato = df.copy()
        if search:
            df_filtrato = df_filtrato[df_filtrato['Nota'].str.contains(search, case=False, na=False)]
        if filtro_tipo:
            df_filtrato = df_filtrato[df_filtrato['Tipo'].isin(filtro_tipo)]
            
        st.dataframe(df_filtrato.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.info("Ancora nessun dato registrato.")

# --- TAB 3: STATISTICHE E GRAFICI ---
with tabs[2]:
    df = pd.read_csv(DB_FILE)
    if not df.empty:
        # Calcolo Saldi
        entrate = df[df['Tipo'] == 'Entrata']['Importo'].sum()
        uscite = df[df['Tipo'] == 'Uscita']['Importo'].sum()
        totale = entrate - uscite
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Totale Risparmi", f"{totale:.2f} €")
        c2.metric("Entrate", f"{entrate:.2f} €")
        c3.metric("Uscite", f"{uscite:.2f} €", delta=f"-{uscite:.2f}", delta_color="inverse")

        # Grafici
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("**Distribuzione Conti**")
            fig_pie = px.pie(df, values='Importo', names='Conto', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_g2:
            st.write("**Andamento Temporale**")
            df['Data_dt'] = pd.to_datetime(df['Data'])
            df_time = df.sort_values('Data_dt')
            df_time['Cumulativo'] = df_time.apply(lambda x: x['Importo'] if x['Tipo']=='Entrata' else -x['Importo'], axis=1).cumsum()
            fig_line = px.area(df_time, x='Data_dt', y='Cumulativo', labels={'Cumulativo': 'Saldo (€)', 'Data_dt': 'Tempo'})
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Dati insufficienti per i grafici.")

# --- TAB 4: METALLI ---
with tabs[3]:
    st.subheader("Monitoraggio Materie Prime")
    metalli = {
        "Rame (Copper)": "HG=F",
        "Oro (Gold)": "GC=F",
        "Argento (Silver)": "SI=F",
        "Litio (ETF LIT)": "LIT",
        "Palladio": "PA=F"
    }
    
    scelta = st.selectbox("Seleziona Metallo", list(metalli.keys()))
    dati = get_metal_data(metalli[scelta])
    
    if dati is not None:
        prezzo_attuale = dati.iloc[-1].values[0] if isinstance(dati.iloc[-1], pd.Series) else dati.iloc[-1]
        st.metric(f"Prezzo {scelta}", f"{prezzo_attuale:.2f} USD")
        st.line_chart(dati)
    else:
        st.error("Errore nel caricamento dati mercati.")
