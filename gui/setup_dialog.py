"""
Finestra di gestione e installazione portatile dei componenti e di FFmpeg.
Permette a un utente su un PC vergine (con solo Python base) di scaricare e configurare
tutto con un semplice clic, senza dover aprire il terminale o usare comandi complessi.
"""

import threading
import customtkinter as ctk
from typing import Optional, Callable
from core.dep_checker import check_all_components, install_pip_packages
from core.ffmpeg_manager import is_ffmpeg_available, download_portable_ffmpeg

class SetupDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_complete: Optional[Callable[[], None]] = None):
        super().__init__(parent)

        self.title("Stato Componenti & Motori Portatili")
        self.geometry("700x580")
        self.minsize(620, 500)
        self.attributes("-topmost", True)
        self.transient(parent)

        self.on_complete = on_complete
        self.is_busy = False

        # Header
        head = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=10)
        head.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            head,
            text="🛠️ Gestione Componenti e Motori Portatili",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            head,
            text="Verifica e installa automaticamente i motori necessari per decodifica e ricodifica.",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Elenco componenti
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=240)
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=4)

        # Barra di avanzamento per download/pip
        self.prog_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.prog_bar.set(0)
        self.prog_bar.pack(fill="x", padx=16, pady=(6, 2))

        self.status_lbl = ctk.CTkLabel(
            self,
            text="Pronto.",
            font=ctk.CTkFont(size=11),
            text_color="#89b4fa"
        )
        self.status_lbl.pack(anchor="w", padx=18, pady=(0, 4))

        # Console di log interna
        self.log_box = ctk.CTkTextbox(self, height=110, font=ctk.CTkFont(family="Consolas", size=10), fg_color="#11111b")
        self.log_box.pack(fill="x", padx=16, pady=4)

        # Pulsantiera azioni
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=16, pady=12)

        self.install_pip_btn = ctk.CTkButton(
            action_frame,
            text="Installa Moduli Mancanti (pip)",
            fg_color="#e53935",
            hover_color="#c62828",
            font=ctk.CTkFont(weight="bold"),
            command=self._install_missing_pip
        )
        self.install_pip_btn.pack(side="left", padx=(0, 8))

        self.download_ffmpeg_btn = ctk.CTkButton(
            action_frame,
            text="Scarica FFmpeg Portable (1-Click)",
            fg_color="#8957e5",
            hover_color="#7042c1",
            font=ctk.CTkFont(weight="bold"),
            command=self._download_ffmpeg
        )
        self.download_ffmpeg_btn.pack(side="left", padx=(0, 8))

        self.refresh_btn = ctk.CTkButton(
            action_frame,
            text="Aggiorna",
            fg_color="#313244",
            hover_color="#45475a",
            width=80,
            command=self._refresh_status
        )
        self.refresh_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            action_frame,
            text="Chiudi",
            fg_color="#313244",
            hover_color="#45475a",
            width=80,
            command=self.destroy
        )
        close_btn.pack(side="right")

        self._refresh_status()

    def _refresh_status(self):
        """Ricrea la vista dello stato dei componenti."""
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        comps = check_all_components()
        all_ready = True

        for c in comps:
            installed = c["installed"]
            if not installed:
                all_ready = False

            card = ctk.CTkFrame(self.scroll_frame, fg_color="#181825", corner_radius=8)
            card.pack(fill="x", pady=3)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(6, 2))

            name_lbl = ctk.CTkLabel(
                top,
                text=c["name"],
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            )
            name_lbl.pack(side="left")

            cat_lbl = ctk.CTkLabel(
                top,
                text=f"[{c['category']}]",
                font=ctk.CTkFont(size=10),
                text_color="#a6adc8"
            )
            cat_lbl.pack(side="left", padx=8)

            badge = ctk.CTkLabel(
                top,
                text="INSTALLATO ✓" if installed else "MANCANTE ✕",
                fg_color="#26382b" if installed else "#382326",
                text_color="#a6e3a1" if installed else "#f38ba8",
                corner_radius=4,
                font=ctk.CTkFont(size=10, weight="bold"),
                padx=6,
                pady=2
            )
            badge.pack(side="right")

            desc_lbl = ctk.CTkLabel(
                card,
                text=c["desc"],
                font=ctk.CTkFont(size=10),
                text_color="#a6adc8",
                wraplength=620,
                justify="left"
            )
            desc_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        if all_ready:
            self.status_lbl.configure(text="Tutti i componenti e motori sono pronti al 100%!", text_color="#a6e3a1")
        else:
            self.status_lbl.configure(text="Alcuni componenti mancano. Puoi installarli con i pulsanti sottostanti.", text_color="#fab387")

    def _log(self, text: str):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def _install_missing_pip(self):
        if self.is_busy:
            return

        comps = check_all_components()
        missing = [c["pip"] for c in comps if not c["installed"] and c["pip"]]

        if not missing:
            self._log("Tutti i pacchetti Python pip sono già installati!")
            return

        self.is_busy = True
        self.status_lbl.configure(text=f"Installazione di {len(missing)} pacchetti...", text_color="#fab387")
        self.prog_bar.set(0.2)

        def _worker():
            self._log(f"Avvio installazione: {', '.join(missing)}...")
            success = install_pip_packages(missing, self._log)
            self.after(0, lambda: self._on_pip_done(success))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_pip_done(self, success: bool):
        self.is_busy = False
        self.prog_bar.set(1.0 if success else 0.0)
        if success:
            self._log("Installazione pacchetti completata con successo!")
            self.status_lbl.configure(text="Componenti pip installati con successo!", text_color="#a6e3a1")
        else:
            self._log("Si è verificato un errore durante l'installazione.")
            self.status_lbl.configure(text="Errore durante l'installazione pip.", text_color="#f38ba8")

        self._refresh_status()
        if self.on_complete:
            self.on_complete()

    def _download_ffmpeg(self):
        if self.is_busy:
            return

        if is_ffmpeg_available():
            self._log("FFmpeg è già presente e funzionante nel sistema!")
            return

        self.is_busy = True
        self.prog_bar.set(0.05)

        def _prog_cb(pct: int, msg: str):
            self.after(0, lambda: self._update_ffmpeg_progress(pct, msg))

        def _worker():
            self._log("Inizio download automatico di FFmpeg Windows Portable...")
            success = download_portable_ffmpeg(_prog_cb)
            self.after(0, lambda: self._on_ffmpeg_done(success))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_ffmpeg_progress(self, pct: int, msg: str):
        self.prog_bar.set(pct / 100.0)
        self.status_lbl.configure(text=msg, text_color="#89b4fa")
        if pct % 20 == 0:
            self._log(f"FFmpeg: {msg}")

    def _on_ffmpeg_done(self, success: bool):
        self.is_busy = False
        if success:
            self._log("FFmpeg Portable scaricato ed estratto con successo in bin/ffmpeg.exe!")
            self.status_lbl.configure(text="FFmpeg Portable pronto all'uso!", text_color="#a6e3a1")
            self.prog_bar.set(1.0)
        else:
            self._log("Errore durante il download o l'estrazione di FFmpeg.")
            self.status_lbl.configure(text="Errore download FFmpeg.", text_color="#f38ba8")

        self._refresh_status()
        if self.on_complete:
            self.on_complete()
