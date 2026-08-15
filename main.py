# =========================================================================
# GESTIONALE SIMTRACK - BACKEND FASTAPI COMPATIBILE SIMPLYFATT
# File: main.py
# =========================================================================

import sqlite3
import pandas as pd
from io import BytesIO
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="SimTrack API")

DB_NAME = "SimTrack_data.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------------------------------------------------
# INIZIALIZZAZIONE DB (Stesso Schema identico di gestionale_simeda.py)
# -------------------------------------------------------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabella Articoli completa
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articoli (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codice TEXT UNIQUE,
        descrizione TEXT,
        um TEXT DEFAULT 'Pz.',
        listino_1 REAL DEFAULT 0,
        listino_2 REAL DEFAULT 0,
        listino_3 REAL DEFAULT 0,
        listino_4 REAL DEFAULT 0,
        produttore TEXT DEFAULT '',
        categoria TEXT DEFAULT '',
        sottocategoria TEXT DEFAULT '',
        note TEXT DEFAULT '',
        codice_a_barre TEXT DEFAULT '',
        codice_iva TEXT DEFAULT '',
        ubicazione TEXT DEFAULT '',
        codice_fornitore TEXT DEFAULT '',
        cod_articolo_fornitore TEXT DEFAULT '',
        cod_art_fornitore TEXT DEFAULT '',
        fornitore TEXT DEFAULT '',
        cliente TEXT DEFAULT '',
        prezzo_fornitore REAL DEFAULT 0,
        quantita_minima REAL DEFAULT 0,
        dismesso INTEGER DEFAULT 0,
        valuta_sigla TEXT DEFAULT 'EUR',
        colli REAL DEFAULT 0,
        peso_kg REAL DEFAULT 0,
        volume_m3 REAL DEFAULT 0,
        lunghezza_cm REAL DEFAULT 0,
        larghezza_cm REAL DEFAULT 0,
        altezza_cm REAL DEFAULT 0,
        giacenza REAL DEFAULT 0,
        in_arrivo REAL DEFAULT 0,
        fepa_codice_tipo TEXT DEFAULT '',
        fepa_codice_valore TEXT DEFAULT ''
    );
    """)
    
    # Tabella Configurazione Layout Colonne
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config_layout (
        chiave TEXT PRIMARY KEY,
        valore TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Serve la cartella static
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------------------------------------------------
# MODELLI DI DATI PYDANTIC
# -------------------------------------------------------------------------
class ArticoloSchema(BaseModel):
    codice: str
    descrizione: str
    um: Optional[str] = "Pz."
    categoria: Optional[str] = ""
    produttore: Optional[str] = ""
    cod_art_fornitore: Optional[str] = ""
    fornitore: Optional[str] = ""
    cliente: Optional[str] = ""
    listino_1: Optional[float] = 0.0
    listino_2: Optional[float] = 0.0
    listino_3: Optional[float] = 0.0
    listino_4: Optional[float] = 0.0
    prezzo_fornitore: Optional[float] = 0.0
    quantita_minima: Optional[float] = 0.0
    valuta_sigla: Optional[str] = "EUR"
    colli: Optional[float] = 0.0
    peso_kg: Optional[float] = 0.0
    volume_m3: Optional[float] = 0.0
    lunghezza_cm: Optional[float] = 0.0
    larghezza_cm: Optional[float] = 0.0
    altezza_cm: Optional[float] = 0.0
    giacenza: Optional[float] = 0.0

class GiacenzaUpdate(BaseModel):
    giacenza: float

class LayoutConfig(BaseModel):
    colonne: List[str]

class DeleteRequest(BaseModel):
    ids: List[int]

# -------------------------------------------------------------------------
# ROTTE API BACKEND
# -------------------------------------------------------------------------

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/api/articoli")
def get_articoli():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articoli ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/articoli")
def create_articolo(art: ArticoloSchema):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articoli (
                codice, descrizione, um, categoria, produttore, cod_art_fornitore, 
                fornitore, cliente, listino_1, listino_2, listino_3, listino_4, 
                prezzo_fornitore, quantita_minima, valuta_sigla, colli, peso_kg, 
                volume_m3, lunghezza_cm, larghezza_cm, altezza_cm, giacenza
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            art.codice, art.descrizione, art.um, art.categoria, art.produttore, art.cod_art_fornitore,
            art.fornitore, art.cliente, art.listino_1, art.listino_2, art.listino_3, art.listino_4,
            art.prezzo_fornitore, art.quantita_minima, art.valuta_sigla, art.colli, art.peso_kg,
            art.volume_m3, art.lunghezza_cm, art.larghezza_cm, art.altezza_cm, art.giacenza
        ))
        conn.commit()
        return {"status": "success", "message": "Articolo inserito con successo!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Codice articolo già esistente!")
    finally:
        conn.close()

@app.put("/api/articoli/{art_id}/giacenza")
def update_giacenza(art_id: int, data: GiacenzaUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE articoli SET giacenza = ? WHERE id = ?", (data.giacenza, art_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/articoli/delete")
def delete_articoli(req: DeleteRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.executemany("DELETE FROM articoli WHERE id = ?", [(i,) for i in req.ids])
    conn.commit()
    conn.close()
    return {"status": "success", "deleted": len(req.ids)}

# -------------------------------------------------------------------------
# IMPORTAZIONE MULTI-FORMATO SIMPLYFATT (CSV ITALIANO & EXCEL)
# -------------------------------------------------------------------------
@app.post("/api/import-simplyfatt")
async def import_simplyfatt(file: UploadFile = File(...)):
    contents = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".csv"):
            # Gestione avanzata del separatore e dell'encoding italiano SimplyFatt
            try:
                df = pd.read_csv(BytesIO(contents), sep=None, engine='python', encoding='utf-8-sig')
            except Exception:
                df = pd.read_csv(BytesIO(contents), sep=None, engine='python', encoding='latin1')
        else:
            df = pd.read_excel(BytesIO(contents))
            
        conn = get_db()
        cursor = conn.cursor()
        
        nuovi, aggiornati = 0, 0
        
        # Pulizia colonne (rimozione spazi bianchi laterali)
        df.columns = [str(col).strip() for col in df.columns]

        def get_val(row, *keys):
            for k in keys:
                if k in row and pd.notna(row[k]):
                    return row[k]
            return None

        def to_float(val):
            try: return float(val) if val is not None and pd.notna(val) else 0.0
            except: return 0.0

        def to_str(val):
            return str(val).strip() if val is not None and pd.notna(val) and str(val).strip() != "nan" else ""

        for _, r in df.iterrows():
            cod = to_str(get_val(r, "Codice", "codice", "CODICE"))
            if not cod:
                continue

            desc = to_str(get_val(r, "Descrizione", "descrizione", "DESCRIZIONE"))
            um = to_str(get_val(r, "U.M.", "UM", "um", "Unità di misura"))
            l1 = to_float(get_val(r, "Listino 1", "listino_1", "Listino1"))
            l2 = to_float(get_val(r, "Listino 2", "listino_2", "Listino2"))
            l3 = to_float(get_val(r, "Listino 3", "listino_3", "Listino3"))
            l4 = to_float(get_val(r, "Listino 4", "listino_4", "Listino4"))
            prod = to_str(get_val(r, "Produttore", "produttore"))
            cat = to_str(get_val(r, "Categoria", "categoria"))
            cod_forn = to_str(get_val(r, "Cod. Articolo Fornitore", "Cod. Art. Fornitore", "cod_art_fornitore", "cod_articolo_fornitore"))
            p_forn = to_float(get_val(r, "prezzo_fornitore", "Prezzo Fornitore", "Costo Fornitore", "Costo"))
            q_min = to_float(get_val(r, "quantita_minima", "Quantità Minima", "Q.tà Minima", "Scorta Minima"))
            valuta = to_str(get_val(r, "valuta_sigla", "Valuta Sigla", "Valuta"))
            colli = to_float(get_val(r, "Colli", "colli"))
            peso = to_float(get_val(r, "Peso kg", "Peso", "kg", "peso_kg"))
            vol = to_float(get_val(r, "Volume m3", "Volume", "volume_m3"))
            lung = to_float(get_val(r, "Lunghezza cm", "Lunghezza", "lunghezza_cm"))
            larg = to_float(get_val(r, "Larghezza cm", "Larghezza", "larghezza_cm"))
            alt = to_float(get_val(r, "Altezza cm", "Altezza", "altezza_cm"))

            cursor.execute("SELECT id FROM articoli WHERE codice = ?", (cod,))
            esiste = cursor.fetchone()

            if esiste:
                cursor.execute("""
                UPDATE articoli 
                SET descrizione = ?, um = ?, listino_1 = ?, listino_2 = ?, listino_3 = ?, listino_4 = ?,
                    produttore = ?, categoria = ?, cod_art_fornitore = ?, cod_articolo_fornitore = ?, 
                    prezzo_fornitore = ?, quantita_minima = ?, valuta_sigla = ?, colli = ?, 
                    peso_kg = ?, volume_m3 = ?, lunghezza_cm = ?, larghezza_cm = ?, altezza_cm = ?
                WHERE codice = ?
                """, (desc, um, l1, l2, l3, l4, prod, cat, cod_forn, cod_forn, p_forn, q_min, valuta, colli, peso, vol, lung, larg, alt, cod))
                aggiornati += 1
            else:
                cursor.execute("""
                INSERT INTO articoli (
                    codice, descrizione, um, listino_1, listino_2, listino_3, listino_4,
                    produttore, categoria, cod_art_fornitore, cod_articolo_fornitore,
                    prezzo_fornitore, quantita_minima, valuta_sigla, colli, peso_kg, 
                    volume_m3, lunghezza_cm, larghezza_cm, altezza_cm, giacenza
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0)
                """, (cod, desc, um, l1, l2, l3, l4, prod, cat, cod_forn, cod_forn, p_forn, q_min, valuta, colli, peso, vol, lung, larg, alt))
                nuovi += 1

        conn.commit()
        conn.close()
        return {"status": "success", "nuovi": nuovi, "aggiornati": aggiornati}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore lettura file SimplyFatt: {str(e)}")

@app.get("/api/config-layout")
def get_layout():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT valore FROM config_layout WHERE chiave = 'ordine_colonne_magazzino'")
    row = cursor.fetchone()
    conn.close()
    if row and row['valore']:
        return {"colonne": row['valore'].split(",")}
    return {"colonne": []}

@app.post("/api/config-layout")
def save_layout(cfg: LayoutConfig):
    conn = get_db()
    cursor = conn.cursor()
    val_str = ",".join(cfg.colonne)
    cursor.execute("INSERT OR REPLACE INTO config_layout (chiave, valore) VALUES ('ordine_colonne_magazzino', ?)", (val_str,))
    conn.commit()
    conn.close()
    return {"status": "success"}