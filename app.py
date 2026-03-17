import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- 1. SETUP E CONNESSIONE ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

# Caricamento dati dal tuo Google Sheet
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"⚠️ Errore: Assicurati di aver lanciato l'app dalla cartella C:\Gestione_reacto")
    st.stop()

# Configurazione AI Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. INTERFACCIA E GRAFICI (I GRADINI) ---
st.title("📊 Dashboard Ingegneria & Startup")

with st.sidebar:
    st.success(f"📱 Link Telefono: http://{get_ip()}:8501")

if not df.empty:
    # Calcolo saldo reale per i gradini
    df_sorted = df.sort_values('Data').copy()
    # Se è 'Uscita', l'importo diventa negativo per il grafico
    df_sorted['Valore_Reale'] = df_sorted.apply(lambda x: x['Importo'] if x['Tipo'] == 'Entrata' else -x['Importo'], axis=1)
    df_sorted['Saldo_Cumulativo'] = df_sorted['Valore_Reale'].cumsum()
    
    st.subheader("📈 Andamento Liquidità (Cash Flow)")
    st.area_chart(df_sorted.set_index('Data')['Saldo_Cumulativo'])
    
    saldo_startup = df_sorted[df_sorted['Conto'] == 'Risparmi Startup']['Valore_Reale'].sum()
    st.metric("Capitale Startup", f"€ {saldo_startup:,.2f}")

# --- 3. ASSISTENTE AI STRATEGICO ---
st.divider()
st.subheader("🤖 Chiedi all'AI sulla tua Startup")
user_input = st.chat_input("Esempio: 'Analizza le mie uscite e dimmi quanto posso investire'")

if user_input:
    # L'AI legge i tuoi dati reali dal foglio
    contesto = f"Dati: {df.to_string()}. Obiettivo: Startup Ingegneria. Rispondi a: {user_input}"
    with st.chat_message("assistant"):
        response = model.generate_content(contesto)
        st.write(response.text)

# --- 4. REGISTRAZIONE DATI (PER TELEFONO) ---
with st.expander("📝 Registra Nuova Operazione"):
    with st.form("new_data", clear_on_submit=True):
        col1, col2 = st.columns(2)
        f_date = col1.date_input("Data")
        f_tipo = col1.selectbox("Tipo", ["Entrata", "Uscita"])
        f_amt = col2.number_input("Importo (€)", step=0.01)
        f_conto = col2.selectbox("Conto", ["Principale", "Risparmi Startup"])
        f_nota = st.text_input("Nota")
        
        if st.form_submit_button("Salva nel Cloud"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date.strftime('%d/%m/%Y'), "Tipo": f_tipo, "Conto": f_conto, "Importo": f_amt, "Nota": f_nota}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Dato registrato! Ricarica per aggiornare i gradini.")
