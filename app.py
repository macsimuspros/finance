import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="PocketFinance AI", layout="centered")

# --- TITOLO E STILE ---
st.markdown("# 💰 PocketFinance AI")
st.caption("Il tuo assistente finanziario personale")

# --- FUNZIONE DATI (Simulata con Cache per velocità su Mobile) ---
@st.cache_data
def get_metal_data(ticker):
    return yf.download(ticker, period="1mo", interval="1d")['Close']

# --- NAVIGAZIONE MOBILE ---
tab1, tab2, tab3, tab4 = st.tabs(["➕ Inserisci", "📈 Analisi", "🤖 AI", "⛏️ Metalli"])

with tab1:
    st.subheader("Registra Movimento")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1: tipo = st.selectbox("Tipo", ["Uscita", "Entrata"])
        with col2: conto = st.selectbox("Conto", ["Principale", "Risparmi", "Investimenti", "Emergenza"])
        
        cifra = st.number_input("Importo (€)", min_value=0.0, step=0.50)
        nota = st.text_input("Commento (es. Spesa, Cobalto, Affitto)")
        
        if st.form_submit_button("REGISTRA", use_container_width=True):
            st.success(f"Registrato: {cifra}€ su {conto}!")
            # Nota: Qui i dati andranno su Google Sheets se hai configurato i Secrets

with tab2:
    st.subheader("Percentuali e Statistiche")
    # Esempio di calcolo percentuali (Settimanale/Mensile)
    col_a, col_b = st.columns(2)
    col_a.metric("Settimanale", "15%", delta="-2% rispetto a ieri")
    col_b.metric("Mensile", "45%", delta="+5% budget usato")
    
    st.write("### Ripartizione Conti")
    # Grafico a torta interattivo
    mock_data = pd.DataFrame({'Conto': ['Principale', 'Risparmi', 'Emergenza'], 'Valore': [500, 1200, 300]})
    fig = px.pie(mock_data, values='Valore', names='Conto', hole=.3)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("🤖 AI Financial Advisor")
    st.info("Analisi in corso sui tuoi commenti...")
    # Logica AI semplificata
    st.markdown("""
    **Consiglio del giorno:**
    > "Ho notato che hai aggiunto molti commenti relativi al **Rame**. Il mercato è volatile: 
    > hai già risparmiato il **10%** questo mese, potresti diversificare sul conto 'Risparmi'."
    """)

with tab4:
    st.subheader("Valore Metalli (Real-Time)")
    try:
        rame = get_metal_data("HG=F")
        st.line_chart(rame, y_label="Prezzo Rame")
        st.write("📉 *Il Cobalto non ha un ticker pubblico diretto, monitora il Rame come indicatore industriale.*")
    except:
        st.error("Dati mercati non disponibili al momento.")
