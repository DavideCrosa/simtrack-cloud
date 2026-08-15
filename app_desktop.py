# =========================================================================
# GESTIONALE SIMTRACK - LAUNCHER DESKTOP NATIVO (FastAPI + PyWebView)
# Percorso: app_desktop.py
# =========================================================================

import os
import sys
import time
import subprocess
import webview

def start_fastapi():
    # Avvia Uvicorn con main.py sulla porta 8000
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    return subprocess.Popen(cmd)

if __name__ == "__main__":
    print("🚀 Avvio del backend FastAPI (SimTrack)...")
    processo_backend = start_fastapi()
    
    # Attesa per consentire l'avvio del server FastAPI
    time.sleep(2)

    print("🖥️ Apertura interfaccia Desktop...")
    # Apre la finestra nativa sulla porta 8000
    window = webview.create_window(
        title="SimTrack Desktop",
        url="http://127.0.0.1:8000",
        width=1400,
        height=900,
        resizable=True
    )
    
    webview.start()
    
    # Alla chiusura della finestra, termina il server FastAPI
    processo_backend.terminate()