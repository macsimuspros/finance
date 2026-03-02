import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import yfinance as yf

st.set_page_config(page_title="PocketFinance AI", layout="centered")

# --- DATABASE LOCALE (Per ora usiamo questo) ---
conn = sqlite3.connect('finance.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trans (date TEXT, type TEXT, amount REAL, acc TEXT, comm TEXT)''')
conn.commit()

st.title("💰 PocketFinance AI")

# --- NAVIGAZIONE ---
tab1, tab2, tab3 = st.tabs(["➕ Inserisci", "📊 Analisi", "⛏️ Metalli"])

with tab1:
    with st.form("mobile_form", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
        conto = st.selectbox("Conto", ["Principale", "Risparmi", "Carta"])
        cifra = st.number_input("Importo (€)", min_value=0.0, step=1.0)
        nota = st.text_input("Commento")
        if st.form_submit_button("REGISTRA", use_container_width=True):
            c.execute("INSERT INTO trans VALUES (?,?,?,?,?)", (datetime.now().strftime("%Y-%m-%d"), tipo, cifra, conto, nota))
            conn.commit()
            st.success("Registrato!")

with tab2:
    df = pd.read_sql_query("SELECT * FROM trans", conn)
    if not df.empty:
        st.metric("Totale Spese", f"{df[df['type']=='Uscita']['amount'].sum()} €")
        fig = px.bar(df, x='date', y='amount', color='type', title="Andamento")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun dato registrato.")

with tab3:
    st.subheader("Prezzo Rame (Real-time)")
    try:
        data_metal = yf.download("HG=F", period="1mo", interval="1d")
        if not data_metal.empty:
            st.line_chart(data_metal['Close'])
        else:
            st.warning("Dati metalli momentaneamente non disponibili.")
    except Exception as e:
        st.error("Errore nel caricamento metalli.")
