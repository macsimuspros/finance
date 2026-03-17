import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

# Funzione per trovare l'IP locale (per il telefono)
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# --- 2. CONNESSIONE DATI CON GOGGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Lettura dati (assicurati che il foglio si chiami 'Dati')
    df = conn.read(worksheet="Dati")
    
    # Conversione tipi per i grafici
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"⚠️ Errore critico: Controlla il link dello Spreadsheet in secrets.toml e i permessi di condivisione!")
    st.stop()

# --- 3. CONFIGURAZIONE AI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.warning("🤖 AI non configurata. Controlla la GEMINI_API_KEY nel file secrets.")

# --- 4. SIDEBAR & MOBILE LINK ---
with st.sidebar:
    st.title("📱 Mobile Connect")
    local_ip = get_ip()
    st.success(f"Dallo stesso Wi-Fi apri:\nhttp://{local_ip}:8501")
    st.info("Ingegneria Chimica Dashboard")

# --- 5. VISUALIZZAZIONE DATI (I GRADINI) ---
st.title("🧪 ReactoFinance: Controllo Reagenti Finanziari")

if not df.empty:
    # Calcolo Saldo Cumulativo per l'effetto a gradini
    df_sorted = df.sort_values('Data')
    df_sorted['Saldo'] = df_sorted['Importo'].cumsum()
    
    st.subheader("📈 Andamento Saldo Temporale")
    st.line_chart(df_sorted.set_index('Data')['Saldo'])
    
    st.metric("Saldo Attuale", f"€ {df_sorted['Saldo'].iloc[-1]:,.2f}")
else:
    st.info("Nessun dato trovato. Inserisci la tua prima transazione qui sotto!")

# --- 6. ASSISTENTE AI STRATEGICO ---
st.divider()
st.subheader("🤖 Consulta l'AI Finanziaria")
user_input = st.chat_input("Chiedi analisi sulla startup o sulle tue spese...")

if user_input:
    # Creiamo il contesto per Gemini
    context = f"Dati attuali: {df.tail(10).to_string(index=False)}. "
    context += f"Saldo: {df['Importo'].sum()}. Obiettivo: Startup Ingegneria. Rispondi a: {user_input}"
    
    with st.chat_message("assistant"):
        response = model.generate_content(context)
        st.write(response.text)

# --- 7. INPUT NUOVI DATI ---
with st.expander("📝 Registra Movimento"):
    with st.form("entry_form", clear_on_submit=True):
        f_date = st.date_input("Data", datetime.now())
        f_desc = st.text_input("Descrizione")
        f_amt = st.number_input("Importo (€)", step=0.01)
        
        if st.form_submit_button("Salva nel Cloud"):
            new_data = pd.DataFrame([{"ID": len(df)+1, "Data": f_date, "Descrizione": f_desc, "Importo": f_amt}])
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Dato inviato! Ricarica per aggiornare i grafici.")
