import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf
import os
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="PocketFinance AI - Engineering Edition", layout="wide")

# File di database
DB_FILE = "database_finanze.csv"
SETTINGS_FILE = "settings_conti.csv"

# --- FUNZIONI DI SISTEMA ---
def inizializza_files():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Conto', 'Importo', 'Nota']).to_csv(DB_FILE, index=False)
    if not os.path.exists(SETTINGS_FILE):
        # Conti predefiniti per uno studente di ingegneria
        pd.DataFrame({'Conto': ["Principale", "Risparmi Startup", "Emergenza", "Investimenti"]}).to_csv(SETTINGS_FILE, index=False)

def get_lista_conti():
    df_c = pd.read_csv(SETTINGS_FILE)
    return df_c['Conto'].tolist()

def aggiungi_nuovo_conto(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    if nome and nome not in df_c['Conto'].values:
        nuovo = pd.concat([df_c, pd.DataFrame({'Conto': [nome]})], ignore_index=True)
        nuovo.to_csv(SETTINGS_FILE, index=False)
        return True
    return False

def elimina_conto_esistente(nome):
    df_c = pd.read_csv(SETTINGS_FILE)
    df_c = df_c[df_c['Conto'] != nome]
    df_c.to_csv(SETTINGS_FILE, index=False)

@st.cache_data(ttl=3600)
def get_metal_data(ticker):
    try:
        data = yf.download(ticker, period="1mo
