import streamlit as st
import os
import socket
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai

# --- 1. FORZATURA PERCORSO ASSOLUTO ---
# Invece di controllare dove sei, diciamo noi a Streamlit dove guardare
current_dir = "C:/Gestione_reacto"
os.environ["STREAMLIT_CONFIG_DIR"] = f"{current_dir}/.streamlit"

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

# --- 3. CONNESSIONE DATI (GOOGLE SHEETS) ---
try:
    # Questa è la funzione che legge i segreti da .streamlit/secrets.toml
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    
    # Pulizia dati per i grafici
    df.columns = df.columns.str.strip()
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"Impossibile leggere i segreti. Verifica che il file C:/Gestione_reacto/.streamlit/secrets.toml esista.")
    st.exception(e)
    st.stop()

# --- 4. CONFIGURAZIONE AI GEMINI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.warning("⚠️ Errore AI: Chiave API non trovata o non valida.")

# --- 5. INTERFACCIA E GRAFICI A GRADINI ---
st.title("📊 Dashboard Startup Reacto")

with st.sidebar:
    st.success(f"📱 Link Telefono: http://{get_ip()}:8501")

if not df.empty:
    # Calcolo saldo per i gradini
    df_sorted = df.sort_values('Data').copy()
    df_sorted['Valore_Vero'] = df_sorted.apply(
        lambda x: x['Importo'] if x['Tipo'] == 'Entrata' else -x['Importo'], axis=1
    )
    df_sorted['Saldo_Cumulativo'] = df_sorted['Valore_Vero'].cumsum()
    
    st.subheader("📈 Andamento Finanziario")
    st.area_chart(df_sorted.set_index('Data')['Saldo_Cumulativo'])
    
    col1, col2 = st.columns(2)
    col1.metric("Saldo Attuale", f"€ {df_sorted['Saldo_Cumulativo'].iloc[-1]:,.2f}")
    col2.metric("N. Operazioni", len(df))

# --- 6. AI CHAT ---
st.divider()
user_input = st.chat_input("Chiedi all'AI un consiglio sulla tua startup...")
if user_input:
    context = f"Dati: {df.tail(5).to_string()}. Saldo: {df['Importo'].sum()}. Rispondi a: {user_input}"
    with st.chat_message("assistant"):
        response = model.generate_content(context)
        st.write(response.text)

# --- 7. FORM DI INSERIMENTO ---
with st.expander("📝 Nuova Operazione"):
    with st.form("new_data", clear_on_submit=True):
        f_date = st.date_input("Data", datetime.now())
        f_tipo = st.selectbox("Tipo", ["Entrata", "Uscita"])
        f_amt = st.number_input("Importo (€)", step=0.01)
        f_conto = st.selectbox("Conto", ["Principale", "Risparmi Startup"])
        f_nota = st.text_input("Nota")
        
        if st.form_submit_button("Registra"):
            new_row = pd.DataFrame([{
                "ID": len(df)+1, "Data": f_date.strftime('%d/%m/%Y'), 
                "Tipo": f_tipo, "Conto": f_conto, "Importo": f_amt, "Nota": f_nota
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Dato salvato!")
            st.rerun()
