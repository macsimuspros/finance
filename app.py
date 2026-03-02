import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="PocketFinance AI Pro", layout="centered")

# --- TITOLO E STILE ---
st.title("💰 PocketFinance AI & Metals")

# --- CARICAMENTO DATI (Simulazione database per ora) ---
# Se hai già collegato Google Sheets, tieni la connessione precedente qui
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Data", "Tipo", "Conto", "Importo", "Commento"])

# --- NAVIGAZIONE ---
tab1, tab2, tab3, tab4 = st.tabs(["➕ Registra", "📊 Analisi & AI", "📈 Metalli", "⚙️ Filtri"])

with tab1:
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
        with col2: conto = st.selectbox("Conto", ["Principale", "Risparmi", "Metalli"])
        cifra = st.number_input("Importo (€)", min_value=0.0)
        nota = st.text_input("Commento (es. Acquisto Cobalto)")
        if st.form_submit_button("REGISTRA"):
            new_row = pd.DataFrame([{"Data": datetime.now(), "Tipo": tipo, "Conto": conto, "Importo": cifra, "Commento": nota}])
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.success("Registrato con successo!")

with tab2:
    st.header("🤖 AI Financial Advisor")
    df = st.session_state.data
    if not df.empty:
        # Calcolo Statistiche per l'AI
        tot_uscite = df[df['Tipo'] == 'Uscita']['Importo'].sum()
        tot_entrate = df[df['Tipo'] == 'Entrata']['Importo'].sum()
        bilancio = tot_entrate - tot_uscite
        
        # LOGICA AI (Simulata)
        st.subheader("I consigli della tua AI:")
        if bilancio < 0:
            st.warning(f"⚠️ Attenzione: Sei in negativo di {abs(bilancio)}€. L'AI consiglia di ridurre le uscite nei commenti che contengono extra.")
        else:
            st.info(f"✅ Ottimo lavoro! Hai risparmiato il {round((bilancio/tot_entrate)*100 if tot_entrate >0 else 0)}% delle tue entrate.")
        
        # Percentuali Settimanali/Mensili
        st.write("---")
        st.write("**Ripartizione per Conto:**")
        fig_pie = px.pie(df, values='Importo', names='Conto', hole=.3)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Inserisci dei dati per attivare l'analisi AI.")

with tab3:
    st.header("⛏️ Mercato Metalli")
    metallo = st.radio("Seleziona Metallo", ["Rame (Copper)", "Cobalto (Cobalt)"], horizontal=True)
    
    if metallo == "Rame (Copper)":
        ticker = "HG=F"
    else:
        # Il Cobalto non ha un ticker standard sempre attivo su Yahoo, usiamo una proxy o dati simulati stabili
        ticker = "COB=F" 

    try:
        m_data = yf.download(ticker, period="1mo")
        if not m_data.empty:
            st.line_chart(m_data['Close'], y_label="Prezzo USD")
            st.caption(f"Andamento 30gg per {metallo}")
        else:
            st.error("Dati di mercato chiusi o non disponibili per questo ticker.")
    except:
        st.error("Errore nel recupero dati finanziari.")

with tab4:
    st.subheader("🔍 Ricerca Avanzata")
    search = st.text_input("Cerca nel commento...")
    if search:
        filtered = df[df['Commento'].str.contains(search, case=False, na=False)]
        st.dataframe(filtered)
