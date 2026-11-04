"""
desktop_main.py
===============
Vstupní spouštěcí bod desktopové aplikace AuraEnergy OS (Windows Native Desktop App).
Spouští lokální výpočetní jádro a zapouzdřuje rozhraní do nativního Windows okna bez nutnosti webového prohlížeče.
"""

import sys
import threading
import time
import os

# Import lokálního serveru
import server

def start_server_thread():
    """Spustí backendový HTTP/REST server na pozadí."""
    server.run()

def run_desktop():
    # 1. Spuštění serveru ve vlákně
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    time.sleep(0.8) # Krátká prodleva pro inicializaci socketu

    # 2. Kontrola dostupnosti pywebview
    try:
        import webview
        print("[AuraEnergy OS] Spouštím nativní Windows Desktop aplikaci...")
        window = webview.create_window(
            title="AuraEnergy OS - Desktop Engineering Suite (RETScreen & SAM Replacement)",
            url="http://127.0.0.1:8080",
            width=1480,
            height=920,
            resizable=True,
            confirm_close=True
        )
        webview.start()
    except ImportError:
        print("[AuraEnergy OS] pywebview není k dispozici, otevírám výchozí systémové okno...")
        import webbrowser
        webbrowser.open("http://127.0.0.1:8080")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("[AuraEnergy OS] Aplikace ukončena.")

if __name__ == "__main__":
    run_desktop()
