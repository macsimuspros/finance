import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="PocketFinance AI Pro", layout="centered")

# Connessione a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

st.title("💰 PocketFinance AI")

tab1, tab2, tab3, tab4 = st.tabs(["➕ Registra", "📊 Analisi", "⛏️ Metalli", "🤖 AI Coach"])

with tab1:
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
        with col2: conto = st.selectbox("Conto", ["Banca", "Contanti", "Risparmi"])
        cifra = st.number_input("Importo (€)", min_value=0.0)
        nota = st.text_input("Commento (es. Spesa, Stipendio, Rame)")
        if st.form_submit_button("SALVA", use_container_width=True):
            new_row = pd.DataFrame([{"Data": pd.Timestamp.now().strftime("%Y-%m-%d"), "Tipo": tipo, "Conto": conto, "Importo": cifra, "Commento": nota}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Dato archiviato con successo!")

with tab2:
    if not df.empty:
        df['Importo'] = pd.to_numeric(df['Importo'])
        st.metric("Saldo Totale", f"{df[df['Tipo']=='Entrata']['Importo'].sum() - df[df['Tipo']=='Uscita']['Importo'].sum()} €")
        st.subheader("Ultime 5 operazioni")
        st.table(df.tail(5))
        st.bar_chart(df[df['Tipo']=='Uscita'], x='Data', y='Importo')

with tab3:
    st.subheader("Monitoraggio Metalli")
    rame = yf.download("HG=F", period="1mo")['Close']
    st.line_chart(rame, title="Andamento Rame")

with tab4:
    st.subheader("Consulente AI Personale")
    if st.button("Analizza le mie finanze"):
        if not df.empty:
            tot_u = df[df['Tipo']=='Uscita']['Importo'].sum()
            st.write(f"🤖 **Analisi AI:** Hai speso un totale di {tot_u}€. ")
            # Logica AI per consigli
            if tot_u > 500:
                st.warning("Attenzione: Le tue uscite superano la soglia di sicurezza impostata. Riduci le spese extra.")
            else:
                st.success("Ottima gestione! Sei in linea con i tuoi obiettivi di risparmio.")
        else:
            st.info("Inserisci dei dati per ricevere un'analisi.")
