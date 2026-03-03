import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="PocketFinance AI - Engineering Edition", layout="wide")

# File di database
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

# --- FUNZIONI DI SISTEMA ---
def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        # Conti predefiniti per uno studente di ingegneria
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

def get_lista_conti():
    df_c = pd.read_csv(SETTINGS_FILE)
    return df_c['Conto'].tolist()

def aggiungi_nuovo_conto(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    if nome and nome not in df_c['Conto'].values:
        nuovo = pd.concat([df_c, pd.DataFrame({'Conto': [nome]})], ignore_index=True)
        nuovo.to_csv(SETTINGS_FILE, index=False)
        return True
    return False

def elimina_conto_esistente(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    df_c = df_c[df_c['Conto'] != nome]
    df_c.to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not data.empty:
            # Pulizia dati per evitare errori di formato con Streamlit Line Chart
            df_close = data['Close'].reset_index()
            df_close.columns = ['Date', 'Price']
            return df_close
        return None
    except:
        return None

# Esegui inizializzazione
inizializza_files()

# --- INTERFACCIA UTENTE ---
st.title("💰 PocketFinance AI Pro")
st.markdown("---")

# Menu principale in Tab
tab_ins, tab_gest, tab_conti, tab_metalli = st.tabs([
    "➕ Nuovo Movimento", 
    "🔍 Ricerca & Modifica", 
    "🏦 Gestione Conti", 
    "⛏️ Mercato Metalli"
])

# --- TAB 1: INSERIMENTO ---
with tab_ins:
    st.subheader("Registra Entrata o Uscita")
    with st.form("form_movimento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo operazione", ["Uscita", "Entrata"])
            conto_scelto = st.selectbox("Seleziona Conto", get_lista_conti())
        with col2:
            importo = st.number_input("Importo (€)", min_value=0.0, step=0.01, format="%.2f")
            nota = st.text_input("Nota (es: Acquisto reagenti, Affitto, Borsa di studio)")
        
        submit = st.form_submit_button("SALVA MOVIMENTO")
        
        if submit:
            df = pd.read_csv(DB_FILE)
            # Genera ID univoco
            nuovo_id = int(df['ID'].max() + 1) if not df.empty else 1
            nuova_riga = pd.DataFrame([[
                nuovo_id, 
                datetime.now().strftime("%Y-%m-%d %H:%M"), 
                tipo, 
                conto_scelto, 
                importo, 
                nota
            ]], columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
            
            pd.concat([df, nuova_riga], ignore_index=True).to_csv(DB_FILE, index=False)
            st.success(f"Movimento ID {nuovo_id} salvato correttamente!")

# --- TAB 2: RICERCA E CANCELLAZIONE ---
with tab_gest:
    st.subheader("Storico Movimenti")
    df_view = pd.read_csv(DB_FILE)
    
    if not df_view.empty:
        # Filtri di ricerca
        c_f1, c_f2 = st.columns([2, 1])
        with c_f1:
            query = st.text_input("Cerca nelle note...")
        with c_f2:
            f_conto = st.multiselect("Filtra per conto", get_lista_conti())
        
        # Logica filtri
        df_display = df_view.copy()
        if query:
            df_display = df_display[df_display['Nota'].str.contains(query, case=False, na=False)]
        if f_conto:
            df_display = df_display[df_display['Conto'].isin(f_conto)]
        
        st.dataframe(df_display.sort_values(by="ID", ascending=False), use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🗑️ Elimina o Modifica")
        col_del1, col_del2 = st.columns([1, 2])
        id_da_eliminare = col_del1.number_input("Inserisci ID movimento", min_value=0, step=1)
        if col_del2.button("ELIMINA DEFINITIVAMENTE", type="primary"):
            df_view = df_view[df_view['ID'] != id_da_eliminare]
            df_view.to_csv(DB_FILE, index=False)
            st.warning(f"Movimento {id_da_eliminare} eliminato.")
            st.rerun()
    else:
        st.info("Nessun movimento registrato.")

# --- TAB 3: GESTIONE CONTI ---
with tab_conti:
    st.subheader("I tuoi conti attivi")
    lista_c = get_lista_conti()
    
    for c in lista_c:
        col_c1, col_c2 = st.columns([3, 1])
        col_c1.info(f"🏦 **{c}**")
        if col_c2.button(f"Elimina {c}", key=f"del_{c}"):
            if len(lista_c) > 1:
                elimina_conto_esistente(c)
                st.rerun()
            else:
                st.error("Devi avere almeno un conto attivo.")

    st.divider()
    st.subheader("➕ Aggiungi un nuovo conto")
    nuovo_nome = st.text_input("Nome del conto (es. Satispay, Broker Estero)")
    if st.button("Crea Conto"):
        if aggiungi_nuovo_conto(nuovo_nome):
            st.success("Conto creato!")
            st.rerun()

# --- TAB 4: METALLI (MIGLIORATO) ---
with tab_metalli:
    st.subheader("Monitoraggio Commodity Strategiche")
    
    metalli_config = {
        "Rame (Copper)": "HG=F",
        "Oro (Gold)": "GC=F",
        "Argento (Silver)": "SI=F",
        "Litio (LIT ETF)": "LIT",
        "Nichel (Nickel)": "NI=F",
        "Platino (Platinum)": "PL=F"
    }
    
    scelta_m = st.selectbox("Scegli il metallo", list(metalli_config.keys()))
    ticker_m = metalli_config[scelta_m]
    
    dati_m = get_metal_data(ticker_m)
    
    if dati_m is not None:
        ultimo_prezzo = dati_m['Price'].iloc[-1]
        st.metric(label=f"Prezzo {scelta_m} (USD)", value=f"{float(ultimo_prezzo):.2f}")
        # Grafico Plotly per estetica migliore
        fig_m = px.line(dati_m, x='Date', y='Price', title=f"Trend 30gg: {scelta_m}")
        st.plotly_chart(fig_m, use_container_width=True)
    else:
        st.error(f"Dati non disponibili per {scelta_m}. Il mercato potrebbe essere chiuso.")

