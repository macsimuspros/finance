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

# --- 2. STILE CSS NEON BLUE ---
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stMetric"] { background: rgba(0, 119, 255, 0.1); border: 2px solid #0077ff; border-radius: 15px; padding: 15px; }
    h1, h2, h3 { color: #0077ff !important; text-shadow: 0 0 10px #0077ff; }
    .stButton>button { background-color: #0077ff; color: white; border-radius: 20px; border: none; font-weight: bold; width: 100%; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #0077ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA DATI ---
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

def get_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        df = pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota'])
        df.to_csv(DB_FILE, index=False)
        return df
    df = pd.read_csv(DB_FILE)
    df['Importo'] = pd.to_numeric(df['Importo'], errors='coerce').fillna(0.0)
    df = df.reset_index(drop=True)
    df['ID'] = df.index + 1
    return df

def get_settings():
    if not os.path.exists(SETTINGS_FILE):
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Laboratorio"]}).to_csv(SETTINGS_FILE, index=False)
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

# Saldo Attuale
saldo = df_db[df_db['Tipo'] == 'Entrata']['Importo'].sum() - df_db[df_db['Tipo'] == 'Uscita']['Importo'].sum()

# --- 4. HEADER ---
st.title("🧪 ReactoFinance AI")
st.write(f"### 🚀 Capitale Startup: **€ {saldo:,.2f}** / € 50.000")
st.progress(min(max(saldo/50000, 0.0), 1.0))

tab1, tab2, tab3, tab4 = st.tabs(["📊 GESTIONE", "🤖 REACTOBOT", "⛏️ METALLI PRO", "⚙️ SETUP"])

# --- TAB 1: GESTIONE (RICERCA E FILTRI) ---
with tab1:
    col_in, col_list = st.columns([1, 2])
    with col_in:
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
        st.subheader("🗑️ Elimina")
        id_del = st.number_input("ID Movimento", min_value=1, step=1)
        if st.button("ELIMINA"):
            df_db = df_db[df_db['ID'] != id_del]
            df_db.to_csv(DB_FILE, index=False)
            st.rerun()

    with col_list:
        st.subheader("🔍 Registro & Filtri")
        f_col1, f_col2 = st.columns([2, 1])
        search = f_col1.text_input("Cerca nota...", "")
        f_tipo = f_col2.selectbox("Tipo", ["Tutti", "Entrata", "Uscita"])
        
        df_f = df_db.copy()
        if search:
            df_f = df_f[df_f['Nota'].str.contains(search, case=False, na=False)]
        if f_tipo != "Tutti":
            df_f = df_f[df_f['Tipo'] == f_tipo]
            
        st.dataframe(df_f.sort_values("ID", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: CHAT AI ---
with tab2:
    if "messages" not in st.session_state: st.session_state.messages = []
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if p := st.chat_input("Chiedi analisi flussi..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"): st.markdown(p)
        resp = f"Analisi ReactoFinance: Saldo corrente € {saldo:.2f}. Stai mantenendo la stabilità chimica dei tuoi risparmi."
        with st.chat_message("assistant"): st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})

# --- TAB 3: TUTTI I METALLI (COMPLETO) ---
with tab3:
    st.subheader("⛏️ Quotazioni Industriali (Live)")
    # Dizionario Metalli: [Ticker Yahoo, Fattore di conversione in KG]
    metals_info = {
        "Rame (Cu)": ["HG=F", 2.20462],      # USD/lb -> USD/kg
        "Oro (Au)": ["GC=F", 32.1507],       # USD/oz -> USD/kg
        "Argento (Ag)": ["SI=F", 32.1507],    # USD/oz -> USD/kg
        "Nichel (Ni)": ["NI=F", 2.20462],    # USD/lb -> USD/kg
        "Litio (Index)": ["LTHM", 1.0]        # Indice $/kg
    }
    
    m_sel, m_val = st.columns([1, 2])
    with m_sel:
        s_met = st.selectbox("Seleziona Metallo", list(metals_info.keys()))
        info = metals_info[s_met]
        try:
            m_ticker = yf.download(info[0], period="1d", progress=False)
            u_price = float(m_ticker['Close'].iloc[-1].squeeze())
            
            p_usd_kg = u_price * info[1]
            p_eur_kg = p_usd_kg / eurusd
            
            st.metric("Prezzo EURO", f"€ {p_eur_kg:.2f} / kg")
            st.metric("Prezzo DOLLARI", f"$ {p_usd_kg:.2f} / kg")
            st.caption(f"Cambio: 1€ = {eurusd:.4f}$")
        except: st.error("Errore dati live.")
    
    with m_val:
        try:
            h_data = yf.download(info[0], period="6mo", progress=False)['Close'].reset_index()
            h_data.columns = ['Data', 'Valore']
            fig = px.line(h_data, x='Data', y='Valore', title=f"Trend 6 Mesi {s_met} (USD)")
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='#0077ff')
            st.plotly_chart(fig, use_container_width=True)
        except: st.write("Grafico non disponibile.")

# --- TAB 4: SETUP ---
with tab4:
    st.subheader("⚙️ Configurazione")
    new_c = st.text_input("Aggiungi Conto")
    if st.button("AGGIUNGI"):
        if new_c:
            pd.concat([df_conti, pd.DataFrame({'Conto': [new_c]})], ignore_index=True).to_csv(SETTINGS_FILE, index=False)
            st.rerun()
    st.markdown("---")
    if st.button("⚠️ RESET DATABASE"):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
        st.rerun()
