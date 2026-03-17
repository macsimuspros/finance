import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

# Funzione per trovare l'IP del PC (per il collegamento telefono)
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- CONNESSIONE DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
except Exception as e:
    st.error(f"Errore caricamento dati: {e}. Controlla il nome del foglio Google!")
    st.stop()

# --- CONFIGURAZIONE AI ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("API Key mancante in secrets.toml!")

# --- SIDEBAR (INFO TELEFONO) ---
with st.sidebar:
    st.title("📱 Collegamento Mobile")
    ip_attuale = get_ip()
    st.success(f"Dallo stesso Wi-Fi, apri sul telefono:\nhttp://{ip_attuale}:8501")
    st.info("Ingegneria Chimica & Startup")

# --- DASHBOARD ---
st.title("📊 La tua Dashboard Finanziaria")

# GRAFICO A GRADINI
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'])
    df_chart = df.sort_values('Data')
    df_chart['Saldo_Progressivo'] = df_chart['Importo'].cumsum()
    st.subheader("📈 Andamento Saldo (Effetto Gradini)")
    st.area_chart(df_chart.set_index('Data')['Saldo_Progressivo'])

# --- CHAT AI CONTESTUALE ---
st.divider()
st.subheader("🤖 Chiedi all'Assistente AI")
user_question = st.text_input("Esempio: 'Com'è andata la mia settimana?'")

if user_question:
    # L'AI legge i dati reali dal foglio
    contesto = f"Dati attuali: {df.to_string(index=False)}. Rispondi alla domanda: {user_question}"
    with st.spinner("Analisi in corso..."):
        response = model.generate_content(contesto)
        st.write(response.text)

# --- INPUT DATI ---
with st.expander("📝 Registra Nuova Transazione"):
    with st.form("entry_form"):
        f_date = st.date_input("Data")
        f_desc = st.text_input("Descrizione")
        f_amt = st.number_input("Importo (€)")
        if st.form_submit_button("Salva"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date, "Descrizione": f_desc, "Importo": f_amt}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Sincronizzato!")
            st.rerun()
