import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Creiamo la connessione usando l'URL che hai messo nei Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Leggiamo i dati (il foglio deve chiamarsi "Dati")
df_db = conn.read(worksheet="Dati")

st.title("Dashboard Finanziaria Startup")
st.write("Dati caricati correttamente dal Cloud!")
st.dataframe(df_db)
import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime
from PIL import Image

# --- 1. CONFIGURAZIONE IDENTITY ---
def setup_identity():
    icona_path = "logo.png"
    try:
        if os.path.exists(icona_path):
            img = Image.open(icona_path)
            st.set_page_config(page_title="ReactoFinance", page_icon=img, layout="wide")
        else:
            st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")
    except:
        st.set_page_config(page_title="ReactoFinance", page_icon="🧪", layout="wide")

setup_identity()

# --- 2. STILE CSS NEON ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] { background: rgba(0, 119, 255, 0.1); border: 2px solid #0077ff; border-radius: 15px; padding: 15px; }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DATABASE (AUTO-RIPARANTE) ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def get_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
        return df
    df = pd.read_csv(DB_FILE)
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
    df = df.dropna(subset=['Tipo'])
    df = df.reset_index(drop=True)
    df['ID'] = df.index + 1
    return df

def get_settings():
    if not os.path.exists(SETTINGS_FILE) or os.stat(SETTINGS_FILE).st_size == 0:
        df = pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Laboratorio"]})
        df.to_csv(SETTINGS_FILE, index=False)
        return df
    return pd.read_csv(SETTINGS_FILE)

@st.cache_data(ttl=3600)
def get_eurusd_rate():
    try:
        data = yf.download("EURUSD=X", period="1d", progress=False)
        return float(data['Close'].iloc[-1].squeeze())
    except: return 1.08

df_db = get_db()
df_conti = get_settings()
eurusd = get_eurusd_rate()
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 4. HEADER ---
st.title("🧪 ReactoFinance AI")
st.write(f"🚀 Obiettivo Startup: **€ {saldo:,.2f}** / € 50.000")
st.progress(min(max(saldo/50000, 0.0), 1.0))

# Avviso persistenza dati
if "streamlit" in st.set_page_config.__module__:
    st.warning("⚠️ Nota: Streamlit Cloud resetta i dati dopo lo standby. Usa il tasto BACKUP nel tab SETUP per salvare i dati sul tuo PC.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 GESTIONE", "🤖 REACTOBOT AI", "⛏️ METALLI STRATEGICI", "⚙️ SETUP"])

# --- TAB 1: GESTIONE (Con Ricerca e Filtri) ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("➕ Registra")
        with st.form("new_entry"):
            t = st.selectbox("Tipo", ["Uscita", "Entrata"])
            cnt = st.selectbox("Conto", df_conti['Conto'].tolist())
            val = st.number_input("Valore (€)", min_value=0.0, step=0.01)
            nota = st.text_input("Nota")
            if st.form_submit_button("REGISTRA"):
                new_row = pd.DataFrame([[len(df_db)+1, datetime.now().strftime("%Y-%m-%d"), t, cnt, val, nota]], columns=df_db.columns)
                pd.concat([df_db, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
                st.rerun()
        
        st.markdown("---")
        id_del = st.number_input("ID da eliminare", min_value=1, step=1)
        if st.button("ELIMINA MOVIMENTO"):
            df_db = df_db[df_db['ID'] != id_del]
            df_db.to_csv(DB_FILE, index=False)
            st.rerun()

    with c2:
        st.subheader("🔍 Filtri & Ricerca")
        f_search = st.text_input("Cerca nelle note...")
        f_tipo = st.selectbox("Visualizza", ["Tutti", "Entrata", "Uscita"])
        
        df_f = df_db.copy()
        if f_search:
            df_f = df_f[df_f['Nota'].str.contains(f_search, case=False, na=False)]
        if f_tipo != "Tutti":
            df_f = df_f[df_f['Tipo'] == f_tipo]
            
        st.dataframe(df_f.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: CHAT AI (Analitica) ---
with tab2:
    st.subheader("🤖 ReactoBot Advisor")
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("Chiedi un'analisi dei tuoi risparmi..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        
        if "saldo" in p.lower():
            resp = f"Attualmente disponi di €{saldo:.2f}. Sei al {saldo/500:.2f}% dell'obiettivo startup."
        elif "consiglio" in p.lower():
            resp = "Per raggiungere i 50k in 5 anni, l'analisi chimica dei tuoi flussi suggerisce di accantonare i risparmi derivanti dal lavoro in conti ad alto rendimento."
        else:
            resp = "Sto monitorando le tue finanze per supportare la tua futura idea rivoluzionaria al termine dell'università."
        
        st.session_state.messages.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"): st.markdown(resp)

# --- TAB 3: METALLI (8 TIPI + EURO/KG) ---
with tab3:
    st.subheader("⛏️ Quotazioni Commodity & Metalli Nobili")
    metals_info = {
        "Rame (Cu)": ["HG=F", 2.20462], "Oro (Au)": ["GC=F", 32.1507],
        "Argento (Ag)": ["SI=F", 32.1507], "Nichel (Ni)": ["NI=F", 2.20462],
        "Platino (Pt)": ["PL=F", 32.1507], "Palladio (Pd)": ["PA=F", 32.1507],
        "Cobalto (Co)": ["COB=F", 1.0], "Litio (Li)": ["LTHM", 1.0]
    }
    
    m_sel, m_val = st.columns([1, 2])
    with m_sel:
        s_met = st.selectbox("Seleziona Risorsa", list(metals_info.keys()))
        info = metals_info[s_met]
        try:
            m_ticker = yf.download(info[0], period="1d", progress=False)
            u_price = float(m_ticker['Close'].iloc[-1].squeeze())
            p_usd_kg = u_price * info[1]
            p_eur_kg = p_usd_kg / eurusd
            st.metric("PREZZO EURO/KG", f"€ {p_eur_kg:.2f}")
            st.metric("PREZZO USD/KG", f"$ {p_usd_kg:.2f}")
        except: st.error("Dati live non disponibili.")
    
    with m_val:
        try:
            h_data = yf.download(info[0], period="6mo", progress=False)['Close'].reset_index()
            h_data.columns = ['Data', 'Valore']
            fig = px.line(h_data, x='Data', y='Valore', title=f"Trend {s_met} (USD)")
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
        except: st.write("Grafico offline.")

# --- TAB 4: SETUP (Backup e Gestione Conti) ---
with tab4:
    st.subheader("⚙️ Configurazione & Backup")
    
    # Sezione Backup per non perdere dati
    st.write("### 💾 Protezione Dati")
    csv = df_db.to_csv(index=False).encode('utf-8')
    st.download_button("📥 SCARICA BACKUP CSV (Salva sul PC)", data=csv, file_name=f"backup_finanze_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    
    st.markdown("---")
    c_add, c_del = st.columns(2)
    with c_add:
        st.write("#### Aggiungi Conto")
        new_c = st.text_input("Nome conto")
        if st.button("AGGIUNGI"):
            if new_c:
                pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
                st.rerun()
    with c_del:
        st.write("#### Elimina Conto")
        c_rm = st.selectbox("Seleziona", df_conti['Conto'].tolist())
        if st.button("ELIMINA"):
            df_conti = df_conti[df_conti['Conto'] != c_rm]
            df_conti.to_csv(SETTINGS_FILE, index=False)
            st.rerun()

    if st.button("⚠️ RESET TOTALE DATABASE"):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
        st.rerun()
