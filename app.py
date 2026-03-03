import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="PocketFinance AI - Engineering Pro", layout="wide")

# File di database locali
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

# --- LOGICA DI SISTEMA (INIZIALIZZAZIONE) ---
def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        # Conti iniziali suggeriti per il tuo percorso di 5 anni
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza", "Investimenti Chimica"]}).to_csv(SETTINGS_FILE, index=False)

def get_lista_conti():
    return pd.read_csv(SETTINGS_FILE)['Conto'].tolist()

def aggiungi_nuovo_conto(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    if nome and nome not in df_c['Conto'].values:
        nuovo = pd.concat([df_c, pd.DataFrame({'Conto': [nome]})], ignore_index=True)
        nuovo.to_csv(SETTINGS_FILE, index=False)
        return True
    return False

def elimina_conto_esistente(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    df_c = df_c[df_c['Conto'] != nome].to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        # Scarica dati dell'ultimo mese per analisi tecnica
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not data.empty:
            df_close = data['Close'].reset_index()
            df_close.columns = ['Date', 'Price']
            return df_close
        return None
    except:
        return None

# Esegui i controlli iniziali
inizializza_files()

# --- INTERFACCIA UTENTE ---
st.title("💰 PocketFinance AI: Financial Hub")
st.caption("Strumento di gestione per Ingegneria Chimica & Future Startup")
st.markdown("---")

# Menu principale a Tab
tab_ins, tab_gest, tab_conti, tab_metalli = st.tabs([
    "➕ Inserisci", 
    "🔍 Storico & Modifica", 
    "🏦 Gestione Conti", 
    "⛏️ Mercato Metalli"
])

# --- TAB 1: NUOVO MOVIMENTO ---
with tab_ins:
    st.subheader("Registra Operazione")
    with st.form("form_movimento", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
            conto_scelto = st.selectbox("Conto di riferimento", get_lista_conti())
        with c2:
            importo = st.number_input("Importo (€)", min_value=0.0, step=0.01, format="%.2f")
            nota = st.text_input("Commento (es: Reagenti, Libri, Cobalto)")
        
        if st.form_submit_button("SALVA NEL DATABASE"):
            df = pd.read_csv(DB_FILE)
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
            st.success(f"Movimento salvato con ID: {nuovo_id}")

# --- TAB 2: STORICO, RICERCA E ELIMINAZIONE ---
with tab_gest:
    st.subheader("Gestione Movimenti")
    df_db = pd.read_csv(DB_FILE)
    
    if not df_db.empty:
        # Barra di ricerca e filtri
        col_s1, col_s2 = st.columns([2, 1])
        search_query = col_s1.text_input("Cerca tra le note...")
        filtro_c = col_s2.multiselect("Filtra Conti", get_lista_conti())
        
        df_f = df_db.copy()
        if search_query:
            df_f = df_f[df_f['Nota'].str.contains(search_query, case=False, na=False)]
        if filtro_c:
            df_f = df_f[df_f['Conto'].isin(filtro_c)]
        
        st.dataframe(df_f.sort_values(by="ID", ascending=False), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🗑️ Elimina o Modifica")
        col_ed1, col_ed2 = st.columns([1, 2])
        id_target = col_ed1.number_input("Inserisci ID da eliminare", min_value=0, step=1)
        if col_ed2.button("ELIMINA MOVIMENTO SELEZIONATO", type="primary"):
            df_db = df_db[df_db['ID'] != id_target]
            df_db.to_csv(DB_FILE, index=False)
            st.warning(f"ID {id_target} rimosso. L'app si riavvierà.")
            st.rerun()
    else:
        st.info("Nessun dato presente. Inizia dal tab 'Inserisci'.")

# --- TAB 3: GESTIONE CONTI (CREAZIONE/ELIMINAZIONE) ---
with tab_conti:
    st.subheader("I Tuoi Conti Correnti")
    lista_attiva = get_lista_conti()
    
    for c in lista_attiva:
        cols = st.columns([3, 1])
        cols[0].write(f"💼 **{c}**")
        if cols[1].button(f"Elimina {c}", key=f"btn_{c}"):
            if len(lista_attiva) > 1:
                elimina_conto_esistente(c)
                st.rerun()
            else:
                st.error("Deve esserci almeno un conto attivo.")
    
    st.markdown("---")
    st.subheader("➕ Aggiungi Nuovo Conto")
    nuovo_c_nome = st.text_input("Nome conto (es: Satispay, Portafoglio)")
    if st.button("CREA CONTO"):
        if aggiungi_nuovo_conto(nuovo_c_nome):
            st.success("Conto aggiunto!")
            st.rerun()

# --- TAB 4: METALLI (CON COBALTO) ---
with tab_metalli:
    st.subheader("⛏️ Materie Prime e Metalli Strategici")
    
    # Configurazione ticker: Per il Cobalto usiamo Cobalt Blue Holdings come indicatore
    metalli_list = {
        "Rame (Copper)": "HG=F",
        "Oro (Gold)": "GC=F",
        "Argento (Silver)": "SI=F",
        "Litio (LIT ETF)": "LIT",
        "Cobalto (Cobalt Proxy)": "COB.AX",
        "Nichel (Nickel)": "NI=F",
        "Palladio (Palladium)": "PA=F"
    }
    
    scelta = st.selectbox("Seleziona Metallo", list(metalli_list.keys()))
    ticker = metalli_list[scelta]
    dati = get_metal_data(ticker)
    
    if dati is not None and not dati.empty:
        ultimo_prezzo = float(dati['Price'].iloc[-1])
        precedente = float(dati['Price'].iloc[-2]) if len(dati)>1 else ultimo_prezzo
        delta = ultimo_prezzo - precedente
        
        m1, m2 = st.columns([1, 3])
        m1.metric(label=f"Prezzo {scelta}", value=f"{ultimo_prezzo:.2f} USD", delta=f"{delta:.2f}")
        
        with m2:
            fig = px.line(dati, x='Date', y='Price', title=f"Trend 30 Giorni - {scelta}")
            fig.update_traces(line_color='#00d1b2')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error(f"Dati non disponibili per {scelta}. Controlla la connessione o riprova.")

