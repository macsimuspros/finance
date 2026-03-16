import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import socket

# --- 1. CONFIGURAZIONE E LAYOUT ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide", initial_sidebar_state="collapsed")

# Funzione per ottenere l'IP locale (necessaria per il collegamento telefono)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# --- 2. CONNESSIONE DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    # Pulizia dati per evitare errori nei grafici
    df['Data'] = pd.to_datetime(df['Data'])
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error(f"Errore caricamento database: {e}")
    st.stop()

# --- 3. CONFIGURAZIONE AI ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash') # Versione veloce per mobile

# --- 4. SIDEBAR & CONNESSIONE TELEFONO ---
with st.sidebar:
    st.header("⚙️ System Status")
    local_ip = get_local_ip()
    st.success(f"Link Telefono: http://{local_ip}:8501")
    st.info("Obiettivo: Startup Chimica 2030")

# --- 5. DASHBOARD VISIVA (I GRADINI) ---
st.title("📊 ReactoFinance Dashboard")

if not df.empty:
    # Calcolo saldo cumulativo per l'effetto "a gradini"
    df_chart = df.sort_values('Data').copy()
    df_chart['Saldo'] = df_chart['Importo'].cumsum()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("### Flusso di Cassa (Cash Flow)")
        # Grafico ad area con gradini
        st.area_chart(df_chart.set_index('Data')['Saldo'])
    
    with col2:
        saldo_attuale = df_chart['Saldo'].iloc[-1]
        st.metric("Saldo Attuale", f"€ {saldo_attuale:,.2f}")
        st.metric("Transazioni", len(df))

# --- 6. INTEGRAZIONE AI AVANZATA ---
st.divider()
st.subheader("🤖 Assistente Strategico Startup")

# L'AI legge i tuoi dati e i tuoi obiettivi salvati
prompt_contestuale = f"""
Sei l'assistente finanziario di un futuro ingegnere chimico. 
Obiettivo dell'utente: Lavorare durante i 5 anni di studio, registrare entrate/uscite, laurearsi e fondare una startup rivoluzionaria.
Dati Finanziari Reali (Tabella):
{df.tail(10).to_string(index=False)}
Saldo totale attuale: € {df['Importo'].sum()}
Rispondi in modo tecnico e motivante, tenendo conto che l'utente è un ingegnere.
"""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.chat_input("Chiedi un'analisi o registra un dubbio sulla startup...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)
    
    with st.chat_message("assistant"):
        full_prompt = prompt_contestuale + "\nDomanda utente: " + user_query
        response = model.generate_content(full_prompt)
        st.write(response.text)
        st.session_state.chat_history.append({"q": user_query, "r": response.text})

# --- 7. INPUT RAPIDO (OTTIMIZZATO PER TOUCHSCREEN) ---
st.divider()
with st.expander("📝 Registra Movimento (Lavoro/Spese)"):
    with st.form("mobile_form", clear_on_submit=True):
        f_date = st.date_input("Data", datetime.now())
        f_desc = st.text_input("Descrizione")
        f_amt = st.number_input("Importo (€)", step=0.01)
        if st.form_submit_button("Invia al Database"):
            new_row = pd.DataFrame([{"ID": len(df)+1, "Data": f_date, "Descrizione": f_desc, "Importo": f_amt}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Sincronizzato!")
            st.rerun()
