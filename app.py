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
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Dati")

# --- CONFIGURAZIONE AI ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SIDEBAR (INFO TELEFONO) ---
with st.sidebar:
    st.title("📱 Mobile Link")
    ip_attuale = get_ip()
    st.success(f"Vai su questo link dal telefono:\nhttp://{ip_attuale}:8501")
    st.info("Obiettivo: Startup Ingegneria Chimica")

# --- DASHBOARD ---
st.title("🧪 ReactoFinance: Dashboard Integrata")

# Calcolo saldo cumulativo per i "gradini"
if not df.empty:
    df['Data'] = pd.to_datetime(df['Data'])
    df_chart = df.sort_values('Data')
    df_chart['Saldo_Progressivo'] = df_chart['Importo'].cumsum()
    
    st.subheader("📈 Andamento Finanziario (Gradini)")
    st.area_chart(df_chart.set_index('Data')['Saldo_Progressivo'])

# --- CHAT AI CON MEMORIA DEI DATI ---
st.divider()
st.subheader("🤖 Chiedi alla tua Startup AI")
user_question = st.text_input("Esempio: 'Analizza i miei dati e dimmi se sto risparmiando per la startup'")

if user_question:
    # Qui diamo i dati a Gemini
    contesto_dati = f"Ecco i miei dati finanziari attuali:\n{df.to_string(index=False)}\n\n"
    domanda_completa = contesto_dati + "In base a questi dati, rispondi come un consulente esperto: " + user_question
    
    with st.spinner("L'AI sta elaborando i dati..."):
        response = model.generate_content(domanda_completa)
        st.markdown(f"**Risposta:** {response.text}")

# --- AGGIUNTA DATI (OTTIMIZZATA PER TELEFONO) ---
st.divider()
with st.expander("➕ Inserisci Nuova Spesa/Entrata"):
    with st.form("new_entry"):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            desc = st.text_input("Cosa hai comprato/guadagnato?")
        with col2:
            importo = st.number_input("Importo (€)", format="%.2f")
        
        if st.form_submit_button("Salva nel Cloud"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": data, "Descrizione": desc, "Importo": importo}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Dati inviati! Ricarica per vedere i gradini aggiornati.")
