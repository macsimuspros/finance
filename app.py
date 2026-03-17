import streamlit as st
import os
import socket
from datetime import datetime

# --- FORZA IL PERCORSO DEI SEGRETI (CORRETTO) ---
# Usiamo il percorso assoluto per evitare che Streamlit si perda
os.environ["STREAMLIT_CONFIG_DIR"] = "C:/Gestione_reacto/.streamlit"

from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="ReactoFinance Pro", layout="wide")

# Funzione per trovare l'IP locale per il telefono
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

# --- CONNESSIONE DATI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Dati")
    # Pulizia nomi colonne e conversione tipi
    df.columns = df.columns.str.strip()
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Importo'] = pd.to_numeric(df['Importo'])
except Exception as e:
    st.error("⚠️ Errore di connessione. Assicurati di essere nella cartella C:/Gestione_reacto nel terminale.")
    st.info("Esegui: cd C:/Gestione_reacto prima di lanciare streamlit.")
    st.stop()

# --- CONFIGURAZIONE AI ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.warning("🤖 AI in attesa: Controlla la chiave API in secrets.toml")

# --- SIDEBAR & MOBILE LINK ---
with st.sidebar:
    st.title("📱 Collegamento")
    ip_pc = get_ip()
    st.success(f"Link Telefono:\nhttp://{ip_pc}:8501")
    st.info("Obiettivo: Startup Ingegneria Chimica")

# --- DASHBOARD (I GRADINI) ---
st.title("🧪 ReactoFinance: Controllo Startup")

if not df.empty:
    # Calcolo del saldo cumulativo per l'effetto a gradini
    df_sorted = df.sort_values('Data').copy()
    # Se 'Tipo' è Uscita, l'importo diventa negativo per il grafico
    df_sorted['Valore_Reale'] = df_sorted.apply(
        lambda x: x['Importo'] if x['Tipo'] == 'Entrata' else -x['Importo'], axis=1
    )
    df_sorted['Saldo_Cumulativo'] = df_sorted['Valore_Reale'].cumsum()
    
    st.subheader("📈 Andamento Liquidità (Cash Flow)")
    st.area_chart(df_sorted.set_index('Data')['Saldo_Cumulativo'])
    
    # Metriche principali
    c1, c2, c3 = st.columns(3)
    c1.metric("Capitale Totale", f"€ {df_sorted['Saldo_Cumulativo'].iloc[-1]:,.2f}")
    c2.metric("Risparmi Startup", f"€ {df_sorted[df_sorted['Conto']=='Risparmi Startup']['Valore_Reale'].sum():,.2f}")
    c3.metric("N. Operazioni", len(df))
else:
    st.info("Inserisci la tua prima operazione per attivare i grafici!")

# --- ASSISTENTE AI ---
st.divider()
st.subheader("🤖 Consulta l'AI sulla tua Strategia")
user_query = st.chat_input("Chiedi: 'Analizza le mie spese' o 'Posso investire 100€?'")

if user_query:
    # Diamo all'AI il contesto reale dei tuoi dati
    context = f"Dati attuali: {df.tail(10).to_string()}. Obiettivo: Laurea in 5 anni e Startup. Rispondi a: {user_query}"
    with st.chat_message("assistant"):
        response = model.generate_content(context)
        st.write(response.text)

# --- INPUT NUOVI DATI (OTTIMIZZATO PER MOBILE) ---
with st.expander("📝 Registra Nuova Operazione"):
    with st.form("new_entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        f_date = col1.date_input("Data", datetime.now())
        f_tipo = col1.selectbox("Tipo", ["Entrata", "Uscita"])
        f_amt = col2.number_input("Importo (€)", step=0.01)
        f_conto = col2.selectbox("Conto", ["Principale", "Risparmi Startup"])
        f_nota = st.text_input("Nota/Descrizione")
        
        if st.form_submit_button("Salva nel Cloud"):
            new_row = pd.DataFrame([{
                "ID": len(df)+1, 
                "Data": f_date.strftime('%d/%m/%Y'), 
                "Tipo": f_tipo, 
                "Conto": f_conto, 
                "Importo": f_amt, 
                "Nota": f_nota
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Dati", data=updated_df)
            st.success("Sincronizzazione completata! Ricarica per aggiornare.")
