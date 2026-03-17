import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- 1. CONFIGURAZIONE ---
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
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
        df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error("⚠️ Errore: Controlla permessi Google Sheet e nome scheda 'Dati'!")
    st.stop()

# --- 3. CONFIGURAZIONE AI ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 4. SIDEBAR & TELEFONO ---
with st.sidebar:
    st.title("📱 Mobile Connect")
    st.success(f"Link Telefono: http://{get_ip()}:8501")

# --- 5. GRAFICO A GRADINI ---
st.title("🧪 Dashboard Ingegneria Chimica")
if not df.empty:
    df_sorted = df.sort_values('Data')
    df_sorted['Saldo'] = df_sorted['Importo'].cumsum()
    st.subheader("📈 Andamento Saldo (Effetto Gradini)")
    st.line_chart(df_sorted.set_index('Data')['Saldo'])
    st.metric("Saldo Attuale", f"€ {df_sorted['Saldo'].iloc[-1]:,.2f}")

# --- 6. AI STRATEGICA ---
st.divider()
user_input = st.chat_input("Chiedi alla tua Startup AI...")
if user_input:
    context = f"Dati: {df.tail(5).to_string()}. Saldo: {df['Importo'].sum()}. Rispondi a: {user_input}"
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
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date, "Descrizione": f_desc, "Importo": f_amt}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Sincronizzato!")
            st.rerun()
