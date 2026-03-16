import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Configurazione Pagina
st.set_page_config(page_title="ReactoFinance", page_icon="🚀")

# 2. Connessione Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Lettura Dati sicura
def load_my_data():
    try:
        # Proviamo a leggere il foglio "Dati"
        return conn.read(worksheet="Dati", ttl=0)
    except Exception:
        # Se fallisce, creiamo una tabella vuota per non far crashare l'app
        return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])

df = load_my_data()

# --- INTERFACCIA ---
st.title("🚀 ReactoFinance Dashboard")

if df.empty:
    st.info("Il database è pronto, ma non ci sono ancora movimenti.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- INSERIMENTO ---
with st.expander("➕ Aggiungi Movimento"):
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.selectbox("Tipo", ["Entrata", "Uscita"])
            importo = st.number_input("Importo (€)", min_value=0.0)
        with c2:
            conto = st.text_input("Conto", "Principale")
            nota = st.text_input("Nota")
        
        if st.form_submit_button("REGISTRA NEL CLOUD"):
            nuova_riga = pd.DataFrame([{
                "ID": len(df) + 1,
                "Data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                "Tipo": tipo,
                "Conto": conto,
                "Importo": importo,
                "Nota": nota
            }])
            df_finale = pd.concat([df, nuova_riga], ignore_index=True)
            # Salvataggio su Google Sheets
            conn.update(worksheet="Dati", data=df_finale)
            st.success("Dato salvato correttamente!")
            st.rerun()
