# =========================================================================
# GESTIONALE SIMTRACK - MODULO MAGAZZINO
# Percorso: pages/1_📦_Magazzino.py
# =========================================================================

import io
import sqlite3
import pandas as pd
import streamlit as st

# =========================================================================
# BLOCCO 1: CONFIGURAZIONE PAGINA E TEMA SCURO
# Funzione: Imposta il layout della pagina e lo stile grafico scuro.
# =========================================================================
st.set_page_config(page_title="Magazzino - SimTrack", page_icon="📦", layout="wide")

st.markdown("""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #0e1117 !important;
    color: #ffffff !important;
}
h1, h2, h3, h4, h5, h6, p, label, span, div, .stMarkdown {
    color: #ffffff !important;
}
[data-testid="stForm"], .stExpander {
    background-color: #1e1e24 !important;
    border: 1px solid #31333f !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# BLOCCO 2: CONNESSIONE DATABASE E MIGRAZIONE
# Funzione: Inizializza SQLite e crea le tabelle per i 29 campi dell'anagrafica.
# =========================================================================
conn = sqlite3.connect("SimTrack_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS config_layout (
    chiave TEXT PRIMARY KEY,
    valore TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS articoli (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codice TEXT UNIQUE NOT NULL,
    descrizione TEXT DEFAULT '',
    categoria TEXT DEFAULT '',
    sottocategoria TEXT DEFAULT '',
    note TEXT DEFAULT '',
    codice_iva TEXT DEFAULT '',
    ubicazione TEXT DEFAULT '',
    produttore TEXT DEFAULT '',
    codice_fornitore TEXT DEFAULT '',
    denominazione_fornitore TEXT DEFAULT '',
    cod_art_fornitore TEXT DEFAULT '',
    prezzo_fornitore REAL DEFAULT 0.0,
    listino_1 REAL DEFAULT 0.0,
    listino_2 REAL DEFAULT 0.0,
    listino_3 REAL DEFAULT 0.0,
    listino_4 REAL DEFAULT 0.0,
    valuta TEXT DEFAULT 'EUR',
    um TEXT DEFAULT 'Pz.',
    colli REAL DEFAULT 0.0,
    peso_kg REAL DEFAULT 0.0,
    volume_m3 REAL DEFAULT 0.0,
    lunghezza_cm REAL DEFAULT 0.0,
    larghezza_cm REAL DEFAULT 0.0,
    altezza_cm REAL DEFAULT 0.0,
    dismesso INTEGER DEFAULT 0,
    giacenza REAL DEFAULT 0.0,
    in_arrivo REAL DEFAULT 0.0,
    scorta_minima REAL DEFAULT 0.0,
    valore REAL DEFAULT 0.0
)
""")
conn.commit()

colonne_db_richieste = [
    ("sottocategoria", "TEXT DEFAULT ''"),
    ("note", "TEXT DEFAULT ''"),
    ("codice_iva", "TEXT DEFAULT ''"),
    ("ubicazione", "TEXT DEFAULT ''"),
    ("codice_fornitore", "TEXT DEFAULT ''"),
    ("denominazione_fornitore", "TEXT DEFAULT ''"),
    ("dismesso", "INTEGER DEFAULT 0"),
    ("in_arrivo", "REAL DEFAULT 0.0"),
    ("scorta_minima", "REAL DEFAULT 0.0"),
    ("valore", "REAL DEFAULT 0.0")
]
for col_name, col_type in colonne_db_richieste:
    try:
        cursor.execute(f"ALTER TABLE articoli ADD COLUMN {col_name} {col_type}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# =========================================================================
# BLOCCO 3: SALVATAGGIO AUTOMATICO GIACENZA
# Funzione: Permette la modifica della SOLA giacenza ricalcolando il valore.
# =========================================================================
def salva_modifiche_auto():
    editor_state = st.session_state.get("tabella_articoli_editor", {})
    edited_rows = editor_state.get("edited_rows", {})
    ids_map = st.session_state.get("articoli_ids_map", [])

    if edited_rows and ids_map:
        modificati = 0
        for row_str_idx, changes in edited_rows.items():
            if "giacenza" in changes:
                r_idx = int(row_str_idx)
                if r_idx < len(ids_map):
                    art_id = ids_map[r_idx]
                    nuova_giac = float(changes["giacenza"])
                    
                    cursor.execute("SELECT prezzo_fornitore FROM articoli WHERE id = ?", (art_id,))
                    res = cursor.fetchone()
                    p_forn = res[0] if res else 0.0
                    nuovo_valore = nuova_giac * p_forn

                    cursor.execute(
                        "UPDATE articoli SET giacenza = ?, valore = ? WHERE id = ?", 
                        (nuova_giac, nuovo_valore, art_id)
                    )
                    modificati += 1
        if modificati > 0:
            conn.commit()
            st.toast(f"💾 Giacenza aggiornata per {modificati} articolo/i!", icon="✅")

st.title("📦 Anagrafica Articoli & Gestione Magazzino")
st.markdown("---")

col_left, col_right = st.columns([1, 2.2])

# =========================================================================
# BLOCCO 4: IMPORT ED EXPORT SIMPLYFATT / EXCEL / CSV
# Funzione: Sincronizzazione file SimplyFatt e download report.
# =========================================================================
with col_left:
    st.subheader("📥 Sincronizzazione & Import SimplyFatt")
    st.caption("ℹ️ Sovrascrive anagrafiche e listini. La giacenza SimTrack rimarrà inalterata.")
    
    file_caricato = st.file_uploader("Carica file `.xlsx` o `.csv`", type=["xlsx", "xls", "csv"])

    if file_caricato is not None:
        try:
            df_import = pd.read_csv(file_caricato) if file_caricato.name.endswith(".csv") else pd.read_excel(file_caricato)
            st.info(f"📄 Trovati **{len(df_import)}** articoli pronti per l'importazione.")

            if st.button("🚀 Importa / Aggiorna Anagrafica", type="primary"):
                with st.spinner("⏳ Elaborazione in corso..."):
                    nuovi, aggiornati = 0, 0

                    def to_float(val):
                        try: return float(val) if pd.notna(val) else 0.0
                        except: return 0.0

                    def to_str(val):
                        return str(val).strip() if pd.notna(val) and str(val).strip() != "nan" else ""

                    def to_int(val):
                        try: return int(val) if pd.notna(val) else 0
                        except: return 0

                    for _, r in df_import.iterrows():
                        cod = to_str(r.get("Codice"))
                        if not cod: continue

                        desc = to_str(r.get("Descrizione"))
                        cat = to_str(r.get("Categoria"))
                        sotto_cat = to_str(r.get("Sottocategoria"))
                        note = to_str(r.get("Note"))
                        cod_iva = to_str(r.get("Codice IVA"))
                        ubic = to_str(r.get("Ubicazione"))
                        prod = to_str(r.get("Produttore"))
                        cod_forn = to_str(r.get("Codice Fornitore"))
                        den_forn = to_str(r.get("Denominazione Fornitore"))
                        cod_art_forn = to_str(r.get("Cod. Articolo Fornitore"))
                        p_forn = to_float(r.get("Prezzo Fornitore"))
                        l1 = to_float(r.get("Listino 1"))
                        l2 = to_float(r.get("Listino 2"))
                        l3 = to_float(r.get("Listino 3"))
                        l4 = to_float(r.get("Listino 4"))
                        valuta = to_str(r.get("Valuta", "EUR"))
                        um = to_str(r.get("U.M.", "Pz."))
                        colli = to_float(r.get("Colli"))
                        peso = to_float(r.get("Peso", r.get("kg")))
                        vol = to_float(r.get("Volume m3"))
                        lung = to_float(r.get("Lunghezza cm"))
                        larg = to_float(r.get("Larghezza cm"))
                        alt = to_float(r.get("Altezza cm"))
                        dismesso = to_int(r.get("Dismesso"))
                        in_arrivo = to_float(r.get("In Arrivo"))
                        scorta_min = to_float(r.get("Scorta Minima"))

                        cursor.execute("SELECT id, giacenza FROM articoli WHERE codice = ?", (cod,))
                        esiste = cursor.fetchone()

                        if esiste:
                            giac_attuale = esiste[1]
                            valore_calc = giac_attuale * p_forn
                            cursor.execute("""
                            UPDATE articoli SET
                                descrizione=?, categoria=?, sottocategoria=?, note=?, codice_iva=?, ubicazione=?,
                                produttore=?, codice_fornitore=?, denominazione_fornitore=?, cod_art_fornitore=?,
                                prezzo_fornitore=?, listino_1=?, listino_2=?, listino_3=?, listino_4=?, valuta=?, um=?,
                                colli=?, peso_kg=?, volume_m3=?, lunghezza_cm=?, larghezza_cm=?, altezza_cm=?,
                                dismesso=?, in_arrivo=?, scorta_minima=?, valore=?
                            WHERE codice=?
                            """, (desc, cat, sotto_cat, note, cod_iva, ubic, prod, cod_forn, den_forn, cod_art_forn,
                                  p_forn, l1, l2, l3, l4, valuta, um, colli, peso, vol, lung, larg, alt,
                                  dismesso, in_arrivo, scorta_min, valore_calc, cod))
                            aggiornati += 1
                        else:
                            cursor.execute("""
                            INSERT INTO articoli (
                                codice, descrizione, categoria, sottocategoria, note, codice_iva, ubicazione,
                                produttore, codice_fornitore, denominazione_fornitore, cod_art_fornitore,
                                prezzo_fornitore, listino_1, listino_2, listino_3, listino_4, valuta, um,
                                colli, peso_kg, volume_m3, lunghezza_cm, larghezza_cm, altezza_cm,
                                dismesso, giacenza, in_arrivo, scorta_minima, valore
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0.0,?,?,0.0)
                            """, (cod, desc, cat, sotto_cat, note, cod_iva, ubic, prod, cod_forn, den_forn, cod_art_forn,
                                  p_forn, l1, l2, l3, l4, valuta, um, colli, peso, vol, lung, larg, alt,
                                  dismesso, in_arrivo, scorta_min))
                            nuovi += 1

                    conn.commit()
                st.success(f"🎉 Importazione completata: **{nuovi}** nuovi, **{aggiornati}** aggiornati.")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Errore durante l'importazione: {e}")

    st.markdown("---")
    st.subheader("📤 Esporta Magazzino per SimplyFatt")
    df_exp = pd.read_sql_query("SELECT * FROM articoli", conn)
    if not df_exp.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Magazzino')
        buffer.seek(0)
        st.download_button(
            label="📊 Scarica File Excel (.xlsx)",
            data=buffer,
            file_name="Magazzino_SimplyFatt_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # =========================================================================
    # BLOCCO 5: FORM INSERIMENTO MANUALE COMPLETO
    # Funzione: Form a sezioni espandibili per tutti i 29 campi.
    # =========================================================================
    st.markdown("---")
    st.subheader("➕ Inserimento Manuale Articolo")
    
    with st.form("form_completo", clear_on_submit=True):
        with st.expander("📌 Anagrafica Base", expanded=True):
            f_cod = st.text_input("Codice Articolo*")
            f_desc = st.text_input("Descrizione*")
            c1, c2 = st.columns(2)
            with c1:
                f_cat = st.text_input("Categoria")
                f_um = st.text_input("U.M.", value="Pz.")
            with c2:
                f_subcat = st.text_input("Sottocategoria")
                f_ubic = st.text_input("Ubicazione")
            f_note = st.text_area("Note")

        with st.expander("🏢 Fornitore e Produttore", expanded=False):
            cf1, cf2 = st.columns(2)
            with cf1:
                f_prod = st.text_input("Produttore")
                f_cod_forn = st.text_input("Codice Fornitore")
                f_den_forn = st.text_input("Denominazione Fornitore")
            with cf2:
                f_cod_art_forn = st.text_input("Cod. Articolo Fornitore")
                f_prezzo_forn = st.number_input("Prezzo Fornitore (€)", min_value=0.0, step=0.01)
                f_cod_iva = st.text_input("Codice IVA", value="22")

        with st.expander("💰 Listini Prezzi & Valuta", expanded=False):
            cl1, cl2 = st.columns(2)
            with cl1:
                f_l1 = st.number_input("Listino 1 (€)", min_value=0.0, step=0.01)
                f_l2 = st.number_input("Listino 2 (€)", min_value=0.0, step=0.01)
            with cl2:
                f_l3 = st.number_input("Listino 3 (€)", min_value=0.0, step=0.01)
                f_l4 = st.number_input("Listino 4 (€)", min_value=0.0, step=0.01)
                f_valuta = st.text_input("Valuta", value="EUR")

        with st.expander("📦 Misure, Peso e Logistica", expanded=False):
            ld1, ld2 = st.columns(2)
            with ld1:
                f_colli = st.number_input("Colli", min_value=0.0, step=1.0)
                f_peso = st.number_input("Peso (kg)", min_value=0.0, step=0.01)
                f_vol = st.number_input("Volume (m³)", min_value=0.0, step=0.001)
            with ld2:
                f_lung = st.number_input("Lunghezza (cm)", min_value=0.0, step=0.1)
                f_larg = st.number_input("Larghezza (cm)", min_value=0.0, step=0.1)
                f_alt = st.number_input("Altezza (cm)", min_value=0.0, step=0.1)

        with st.expander("📊 Giacenze, Scorta e Stato", expanded=False):
            sg1, sg2 = st.columns(2)
            with sg1:
                f_giac = st.number_input("Giacenza Iniziale", min_value=0.0, step=1.0)
                f_in_arrivo = st.number_input("In Arrivo", min_value=0.0, step=1.0)
            with sg2:
                f_scorta_min = st.number_input("Scorta Minima", min_value=0.0, step=1.0)
                f_dismesso = st.checkbox("Articolo Dismesso")

        if st.form_submit_button("💾 Salva Articolo Completo", type="primary"):
            if f_cod and f_desc:
                try:
                    f_valore = f_giac * f_prezzo_forn
                    dism_val = 1 if f_dismesso else 0
                    cursor.execute("""
                    INSERT INTO articoli (
                        codice, descrizione, categoria, sottocategoria, note, codice_iva, ubicazione,
                        produttore, codice_fornitore, denominazione_fornitore, cod_art_fornitore,
                        prezzo_fornitore, listino_1, listino_2, listino_3, listino_4, valuta, um,
                        colli, peso_kg, volume_m3, lunghezza_cm, larghezza_cm, altezza_cm,
                        dismesso, giacenza, in_arrivo, scorta_minima, valore
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (f_cod, f_desc, f_cat, f_subcat, f_note, f_cod_iva, f_ubic, f_prod,
                          f_cod_forn, f_den_forn, f_cod_art_forn, f_prezzo_forn, f_l1, f_l2, f_l3, f_l4,
                          f_valuta, f_um, f_colli, f_peso, f_vol, f_lung, f_larg, f_alt,
                          dism_val, f_giac, f_in_arrivo, f_scorta_min, f_valore))
                    conn.commit()
                    st.success(f"✅ Articolo **{f_cod}** salvato con successo!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ Codice articolo già presente!")
            else:
                st.warning("⚠️ Inserisci almeno Codice e Descrizione.")

# =========================================================================
# BLOCCO 6: TABELLA ARTICOLI E COLONNE DINAMICHE
# Funzione: Visualizza la tabella, gestisce filtri e sblocca l'edit solo per Giacenza.
# =========================================================================
with col_right:
    st.subheader("📊 Elenco Articoli Magazzino")

    colonne_totali = [
        "codice", "descrizione", "categoria", "sottocategoria", "note", "codice_iva",
        "ubicazione", "produttore", "codice_fornitore", "denominazione_fornitore",
        "cod_art_fornitore", "prezzo_fornitore", "listino_1", "listino_2", "listino_3",
        "listino_4", "valuta", "um", "colli", "peso_kg", "volume_m3", "lunghezza_cm",
        "larghezza_cm", "altezza_cm", "dismesso", "giacenza", "in_arrivo", "scorta_minima", "valore"
    ]

    cursor.execute("SELECT valore FROM config_layout WHERE chiave = 'ordine_colonne_magazzino'")
    row_cfg = cursor.fetchone()
    if row_cfg and row_cfg[0]:
        colonne_selezionate = [c for c in row_cfg[0].split(",") if c in colonne_totali]
    else:
        colonne_selezionate = colonne_totali.copy()

    with st.expander("⚙️ Gestisci e Personalizza Visibilità Colonne", expanded=False):
        nuove_colonne_sel = st.multiselect(
            "Seleziona ed Ordina le colonne visibili:",
            options=colonne_totali,
            default=colonne_selezionate
        )
        if st.button("💾 Salva Layout Colonne", type="primary"):
            val_str = ",".join(nuove_colonne_sel)
            cursor.execute("INSERT OR REPLACE INTO config_layout (chiave, valore) VALUES ('ordine_colonne_magazzino', ?)", (val_str,))
            conn.commit()
            st.success("✅ Layout salvato!")
            st.rerun()

    cols_fetch = list(dict.fromkeys(["id"] + (nuove_colonne_sel if nuove_colonne_sel else colonne_totali) + ["giacenza"]))
    df_art = pd.read_sql_query(f"SELECT {', '.join(cols_fetch)} FROM articoli", conn)

    if not df_art.empty:
        search_text = st.text_input("🔍 Ricerca rapida (Codice, Descrizione, Categoria, Fornitore)...")
        if search_text:
            camponi = [c for c in ["codice", "descrizione", "categoria", "denominazione_fornitore", "produttore"] if c in df_art.columns]
            if camponi:
                mask = pd.DataFrame([df_art[col].astype(str).str.contains(search_text, case=False, na=False) for col in camponi]).any()
                df_art = df_art[mask]

        df_art = df_art.reset_index(drop=True)
        df_art.insert(0, "Elimina", False)
        st.session_state["articoli_ids_map"] = df_art["id"].tolist()

        config_colonne = {
            "id": None,
            "Elimina": st.column_config.CheckboxColumn("Elimina"),
            "codice": st.column_config.TextColumn("Codice"),
            "descrizione": st.column_config.TextColumn("Descrizione"),
            "categoria": st.column_config.TextColumn("Categoria"),
            "sottocategoria": st.column_config.TextColumn("Sottocategoria"),
            "note": st.column_config.TextColumn("Note"),
            "codice_iva": st.column_config.TextColumn("Cod. IVA"),
            "ubicazione": st.column_config.TextColumn("Ubicazione"),
            "produttore": st.column_config.TextColumn("Produttore"),
            "codice_fornitore": st.column_config.TextColumn("Cod. Forn."),
            "denominazione_fornitore": st.column_config.TextColumn("Denom. Fornitore"),
            "cod_art_fornitore": st.column_config.TextColumn("Cod. Art. Forn."),
            "prezzo_fornitore": st.column_config.NumberColumn("Prezzo Forn. (€)", format="%.2f €"),
            "listino_1": st.column_config.NumberColumn("Listino 1 (€)", format="%.2f €"),
            "listino_2": st.column_config.NumberColumn("Listino 2 (€)", format="%.2f €"),
            "listino_3": st.column_config.NumberColumn("Listino 3 (€)", format="%.2f €"),
            "listino_4": st.column_config.NumberColumn("Listino 4 (€)", format="%.2f €"),
            "valuta": st.column_config.TextColumn("Valuta"),
            "um": st.column_config.TextColumn("U.M."),
            "colli": st.column_config.NumberColumn("Colli", format="%.0f"),
            "peso_kg": st.column_config.NumberColumn("Peso (kg)", format="%.2f"),
            "volume_m3": st.column_config.NumberColumn("Vol. (m³)", format="%.3f"),
            "lunghezza_cm": st.column_config.NumberColumn("Lung. (cm)", format="%.1f"),
            "larghezza_cm": st.column_config.NumberColumn("Larg. (cm)", format="%.1f"),
            "altezza_cm": st.column_config.NumberColumn("Alt. (cm)", format="%.1f"),
            "dismesso": st.column_config.CheckboxColumn("Dismesso"),
            "giacenza": st.column_config.NumberColumn("Giacenza ✏️", format="%.2f", min_value=0.0, step=1.0),
            "in_arrivo": st.column_config.NumberColumn("In Arrivo", format="%.2f"),
            "scorta_minima": st.column_config.NumberColumn("Scorta Min.", format="%.2f"),
            "valore": st.column_config.NumberColumn("Valore Tot. (€)", format="%.2f €"),
        }

        colonne_disabilitate = [c for c in df_art.columns if c not in ["Elimina", "giacenza"]]

        edited_df = st.data_editor(
            df_art,
            hide_index=True,
            use_container_width=True,
            disabled=colonne_disabilitate,
            column_config=config_colonne,
            key="tabella_articoli_editor",
            on_change=salva_modifiche_auto
        )

        da_eliminare = edited_df[edited_df["Elimina"] == True]
        if not da_eliminare.empty:
            if st.button(f"🗑️ Elimina ({len(da_eliminare)}) Articoli Selezionati", type="primary"):
                ids_da_del = da_eliminare["id"].tolist()
                cursor.executemany("DELETE FROM articoli WHERE id = ?", [(i,) for i in ids_da_del])
                conn.commit()
                st.success(f"✅ Cancellati {len(ids_da_del)} articoli.")
                st.rerun()
    else:
        st.info("Nessun articolo presente in magazzino.")