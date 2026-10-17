"""
Punto di ingresso principale per Universal File Converter Portable.
Riconosce automaticamente l'ambiente:
- Se l'ambiente ha già le librerie grafiche moderne (CustomTkinter), avvia l'interfaccia completa.
- Se si trova su un PC con solo Python standard di base, avvia un bootstrapper grafico nativo
  (usando solo il modulo integrato 'tkinter') che permette all'utente di preparare tutto con 1 clic.
"""

import os
import sys

def check_gui_available() -> bool:
    try:
        import customtkinter
        return True
    except ImportError:
        return False

def run_native_bootstrapper():
    """Bootstrapper con Tkinter puro (incluso di default in ogni installazione di Python su Windows)."""
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    import subprocess

    root = tk.Tk()
    root.title("Universal File Converter - Preparazione Portatile")
    root.geometry("560x420")
    root.resizable(False, False)
    root.configure(bg="#181825")

    # Stile TTK scuro
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TProgressbar", thickness=10, troughcolor="#313244", background="#e53935")

    # Intestazione
    hdr = tk.Frame(root, bg="#1e1e2e", padx=20, pady=16)
    hdr.pack(fill="x")

    tk.Label(
        hdr,
        text="Universal File Converter Portable",
        font=("Segoe UI", 16, "bold"),
        fg="#e53935",
        bg="#1e1e2e"
    ).pack(anchor="w")

    tk.Label(
        hdr,
        text="Rilevato ambiente Python di base. Preparazione dei motori di conversione.",
        font=("Segoe UI", 10),
        fg="#a6adc8",
        bg="#1e1e2e"
    ).pack(anchor="w", pady=(4, 0))

    # Corpo
    body = tk.Frame(root, bg="#181825", padx=20, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(
        body,
        text="Per garantire la reale decodifica e ricodifica binaria dei file (immagini, video, audio, dati e documenti) e mostrare l'interfaccia moderna, è necessario scaricare i componenti essenziali.",
        font=("Segoe UI", 10),
        fg="#cdd6f4",
        bg="#181825",
        wraplength=520,
        justify="left"
    ).pack(anchor="w", pady=(0, 12))

    log_box = tk.Text(
        body,
        height=7,
        bg="#11111b",
        fg="#a6adc8",
        font=("Consolas", 9),
        borderwidth=0,
        highlightthickness=1,
        highlightbackground="#313244"
    )
    log_box.pack(fill="x", pady=(0, 10))
    log_box.insert("end", "Pronto per l'installazione automatica dei componenti.\n")

    pbar = ttk.Progressbar(body, style="TProgressbar", mode="indeterminate")
    pbar.pack(fill="x", pady=(0, 12))

    status_var = tk.StringVar(value="Fai clic su 'Prepara ed Avvia' per iniziare.")
    status_lbl = tk.Label(body, textvariable=status_var, font=("Segoe UI", 9), fg="#89b4fa", bg="#181825")
    status_lbl.pack(anchor="w")

    # Pulsanti
    btn_frame = tk.Frame(root, bg="#1e1e2e", padx=20, pady=12)
    btn_frame.pack(fill="x", side="bottom")

    def _log(msg):
        log_box.insert("end", msg + "\n")
        log_box.see("end")

    def _worker():
        pbar.start(10)
        status_var.set("Installazione pacchetti pip in corso...")
        req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
        _log(f"Esecuzione: {' '.join(cmd)}")

        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo
            )
            for line in proc.stdout:
                _log(line.rstrip())
            proc.wait()

            if proc.returncode == 0:
                status_var.set("Installazione riuscita! Avvio dell'applicazione...")
                _log("Tutti i componenti sono stati installati con successo!")
                pbar.stop()
                root.after(1200, _launch_main_app)
            else:
                pbar.stop()
                status_var.set("Errore durante l'installazione pip.")
                start_btn.config(state="normal")
        except Exception as e:
            pbar.stop()
            status_var.set(f"Errore: {e}")
            start_btn.config(state="normal")

    def _launch_main_app():
        root.destroy()
        from gui.app import launch
        launch()

    def _start():
        start_btn.config(state="disabled")
        threading.Thread(target=_worker, daemon=True).start()

    start_btn = tk.Button(
        btn_frame,
        text="Prepara ed Avvia (1-Click)",
        font=("Segoe UI", 10, "bold"),
        bg="#e53935",
        fg="#ffffff",
        activebackground="#c62828",
        activeforeground="#ffffff",
        padx=14,
        pady=6,
        borderwidth=0,
        command=_start
    )
    start_btn.pack(side="right")

    root.mainloop()

def main():
    if "--check" in sys.argv:
        print("[OK] Universal File Converter pronto all'avvio!")
        return

    if check_gui_available():
        from gui.app import launch
        launch()
    else:
        run_native_bootstrapper()

if __name__ == "__main__":
    main()
