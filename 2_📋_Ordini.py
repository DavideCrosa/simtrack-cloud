# =========================================================================
# GESTIONALE SIMTRACK - MODULO ORDINI
# Percorso: pages/2_📄_Ordini.py
# =========================================================================

import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ordini - SimTrack", page_icon="📄", layout="wide")

st.title("📄 Gestione Ordini Clienti & Fornitori")
st.markdown("---")

conn = sqlite3.connect("SimTrack_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ordini (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_ordine TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    cliente_fornitore TEXT DEFAULT '',
    data_ordine TEXT,
    stato TEXT DEFAULT 'Aperto',
    totale REAL DEFAULT 0.0
)
""")
conn.commit()

tab1, tab2 = st.tabs(["📦 Ordini Fornitori", "🛒 Ordini Clienti"])

with tab1:
    st.subheader("Ordini d'Acquisto (Fornitori)")
    df_ordini_f = pd.read_sql_query("SELECT * FROM ordini WHERE tipo = 'Fornitore'", conn)
    if not df_ordini_f.empty:
        st.dataframe(df_ordini_f, use_container_width=True)
    else:
        st.info("Nessun ordine fornitore presente.")

with tab2:
    st.subheader("Ordini di Vendita (Clienti)")
    df_ordini_c = pd.read_sql_query("SELECT * FROM ordini WHERE tipo = 'Cliente'", conn)
    if not df_ordini_c.empty:
        st.dataframe(df_ordini_c, use_container_width=True)
    else:
        st.info("Nessun ordine cliente presente.")