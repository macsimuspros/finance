import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- 1. SETUP PAGINA ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

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

# --- 2. CONNESSIONE DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    # Pulizia nomi colonne e tipi (per evitare errori nei grafici)
    df.columns = df.columns.str.strip()
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"⚠️ Errore Dati: Verifica che il file si chiami 'secrets.toml' e sia nella cartella .streamlit")
    st.stop()

# --- 3. CONFIGURAZIONE AI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.warning("🤖 AI non pronta: Controlla la chiave API!")

# --- 4. SIDEBAR E LINK TELEFONO ---
with st.sidebar:
    st.title("📱 Collegamento")
    ip_pc = get_ip()
    st.success(f"Usa questo link sul cellulare:\nhttp://{ip_pc}:8501")
    st.info("Obiettivo: Startup Chimica 2030")

# --- 5. GRAFICI A GRADINI ---
st.title("🧪 Dashboard Reattore Finanziario")

if not df.empty:
    # Calcolo saldo cumulativo (i gradini)
    df_chart = df.sort_values('Data').copy()
    df_chart['Saldo_Cumulativo'] = df_chart['Importo'].cumsum()
    
    st.subheader("📈 Andamento Saldo nel Tempo")
    st.area_chart(df_chart.set_index('Data')['Saldo_Cumulativo'])
    
    col1, col2 = st.columns(2)
    col1.metric("Saldo Attuale", f"€ {df_chart['Saldo_Cumulativo'].iloc[-1]:,.2f}")
    col2.metric("N. Operazioni", len(df))

# --- 6. INTERFACCIA AI ---
st.divider()
st.subheader("🤖 Assistente Strategico AI")
user_input = st.chat_input("Chiedi un'analisi o un consiglio per la startup...")

if user_input:
    # L'AI legge i dati reali dal tuo foglio
    context = f"Dati utente: {df.tail(10).to_string()}. Saldo: {df['Importo'].sum()}. Rispondi come consulente startup: {user_input}"
    with st.spinner("L'AI sta analizzando i dati..."):
        response = model.generate_content(context)
        st.markdown(f"**AI:** {response.text}")

# --- 7. REGISTRAZIONE RAPIDA ---
with st.expander("📝 Aggiungi Movimento"):
    with st.form("entry", clear_on_submit=True):
        f_date = st.date_input("Data", datetime.now())
        f_desc = st.text_input("Nota (es. Stipendio, Reagenti)")
        f_amt = st.number_input("Importo (€)", step=0.01)
        if st.form_submit_button("Invia al Cloud"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date, "Importo": f_amt, "Nota": f_desc}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Sincronizzato!")
            st.rerun()
