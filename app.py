import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except: IP = '127.0.0.1'
    finally: s.close()
    return IP

# --- CONNESSIONE DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    # Pulizia forzata per i grafici
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"⚠️ Errore: Verifica che secrets.toml sia in C:\Gestione_reacto\.streamlit\secrets.toml")
    st.stop()

# --- CONFIGURAZIONE AI ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- SIDEBAR ---
with st.sidebar:
    st.title("📱 Collegamento Mobile")
    st.success(f"Link: http://{get_ip()}:8501")
    st.info("Obiettivo: Startup Ingegneria Chimica")

# --- DASHBOARD (I GRADINI) ---
st.title("🧪 Dashboard Reattore Finanziario")

if not df.empty:
    # Calcolo saldo reale (Entrate - Uscite) per l'effetto a gradini
    df_chart = df.sort_values('Data').copy()
    # Trasformiamo le Uscite in numeri negativi per il grafico
    df_chart['Valore'] = df_chart.apply(lambda x: x['Importo'] if x['Tipo'] == 'Entrata' else -x['Importo'], axis=1)
    df_chart['Saldo_Cumulativo'] = df_chart['Valore'].cumsum()
    
    st.subheader("📈 Andamento Liquidità")
    st.area_chart(df_chart.set_index('Data')['Saldo_Cumulativo'])
    
    st.metric("Capitale Attuale", f"€ {df_chart['Saldo_Cumulativo'].iloc[-1]:,.2f}")

# --- ASSISTENTE AI ---
st.divider()
st.subheader("🤖 Consulta l'AI sulla tua Startup")
user_query = st.chat_input("Chiedi: 'Analizza il mio capitale per la startup'")

if user_query:
    context = f"Dati attuali: {df.to_string()}. Saldo: {df['Importo'].sum()}. Rispondi come un mentor per una startup di ingegneria: {user_query}"
    with st.chat_message("assistant"):
        response = model.generate_content(context)
        st.write(response.text)

# --- INPUT DATI ---
with st.expander("📝 Registra Nuova Operazione"):
    with st.form("new_op", clear_on_submit=True):
        col1, col2 = st.columns(2)
        f_date = col1.date_input("Data", datetime.now())
        f_tipo = col1.selectbox("Tipo", ["Entrata", "Uscita"])
        f_conto = col2.selectbox("Conto", ["Principale", "Risparmi Startup"])
        f_amt = col2.number_input("Importo (€)", step=0.01)
        f_nota = st.text_input("Nota/Descrizione")
        
        if st.form_submit_button("Invia al Cloud"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date.strftime('%d/%m/%Y'), "Tipo": f_tipo, "Conto": f_conto, "Importo": f_amt, "Nota": f_nota}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Dato salvato! Ricarica la pagina.")
