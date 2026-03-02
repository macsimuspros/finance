import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import yfinance as yf # Per i metalli reali

st.set_page_config(page_title="PocketFinance AI", layout="centered")

# --- DATABASE ---
conn = sqlite3.connect('finance_mobile.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trans (date TEXT, type TEXT, cat TEXT, amount REAL, acc TEXT, comm TEXT)''')
conn.commit()

# --- TABS PER NAVIGAZIONE MOBILE ---
tab1, tab2, tab3, tab4 = st.tabs(["➕ Inserisci", "📊 Analisi", "🤖 AI Advisor", "⛏️ Metalli"])

with tab1:
    st.subheader("Nuova Transazione")
    with st.form("mobile_form", clear_on_submit=True):
        tipo = st.segmented_control("Tipo", ["Entrata", "Uscita"])
        conto = st.selectbox("Conto", ["Principale", "Risparmi", "Crypto/Invest"])
        cifra = st.number_input("Importo (€)", step=1.0)
        nota = st.text_input("A cosa si riferisce? (Commento)")
        if st.form_submit_button("REGISTRA", use_container_width=True):
            c.execute("INSERT INTO trans VALUES (?,?,?,?,?,?)", (datetime.now().date(), tipo, "Generale", cifra, conto, nota))
            conn.commit()
            st.success("Salvato!")

with tab2:
    st.subheader("I tuoi Conti")
    data = pd.read_sql_query("SELECT * FROM trans", conn)
    if not data.empty:
        # Calcolo percentuali automatiche
        entrate = data[data['type']=='Entrata']['amount'].sum()
        uscite = data[data['type']=='Uscita']['amount'].sum()
        st.metric("Bilancio Totale", f"{entrate - uscite} €", delta=f"{entrate} € Entrate")
        
        # Grafico interattivo per mobile
        fig = px.bar(data, x='date', y='amount', color='type', barmode='group', title="Andamento Settimanale")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Chiedi all'AI")
    user_q = st.text_input("Esempio: 'Posso permettermi una cena fuori?'")
    if user_q:
        # Qui collegheresti Gemini o GPT
        st.info("L'AI sta analizzando i tuoi dati... (Simulazione: 'Basato sulle tue uscite di questa settimana, hai ancora 50€ di budget extra!')")

with tab4:
    st.subheader("Mercato Metalli")
    # Esempio Rame (HG=F)
    rame = yf.Ticker("HG=F").history(period="1mo")
    st.line_chart(rame['Close'], title="Andamento Rame (Ultimo Mese)")
    st.caption("Dati aggiornati dai mercati finanziari.")
