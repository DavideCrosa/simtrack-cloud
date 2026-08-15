# =========================================================================
# GESTIONALE SIMTRACK - MODULO DISTINTA BASE
# Percorso: pages/3_⚙️_Distinta_Base.py
# =========================================================================

import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Distinta Base - SimTrack", page_icon="⚙️", layout="wide")

st.title("⚙️ Distinta Base & Componenti")
st.markdown("---")

conn = sqlite3.connect("SimTrack_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS distinta_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice_padre TEXT NOT NULL,
    codice_componente TEXT NOT NULL,
    quantita REAL DEFAULT 1.0,
    note TEXT DEFAULT ''
)
""")
conn.commit()

st.subheader("📋 Componenti Prodotti Assemblati")

df_db = pd.read_sql_query("SELECT * FROM distinta_base", conn)
if not df_db.empty:
    st.dataframe(df_db, use_container_width=True)
else:
    st.info("Nessuna distinta base configurata.")