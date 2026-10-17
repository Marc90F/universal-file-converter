"""
Interfaccia Grafica Principale per il Convertitore Universale Desktop (stile Convertio).
Offre selezione guidata dei file, anteprima metadati, selettori di formato dinamici,
spiegazione dettagliata della conversione binaria e monitoraggio della memoria RAM.
"""

import os
import sys
import psutil
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional

from core.format_registry import get_category, get_compatible_targets, EXTENSION_TO_CATEGORY
from core.orchestrator import ConversionOrchestrator, ConversionTask
from core.dep_checker import check_all_components
from core.ffmpeg_manager import is_ffmpeg_available
from gui.file_card import FileCard
from gui.setup_dialog import SetupDialog

class UniversalConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurazione tema moderno stile Convertio
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Convertitore Universale Desktop - Decoder & Re-encoder")
        self.geometry("1020x740")
        self.minsize(860, 600)

        # Inizializzazione Orchestratore
        self.orchestrator = ConversionOrchestrator()
        self.orchestrator.on_task_update = self._on_task_update_threadsafe
        self.orchestrator.on_task_complete = self._on_task_complete_threadsafe
        self.orchestrator.on_all_completed = self._on_all_completed_threadsafe

        self.file_cards: Dict[str, FileCard] = {}
        self.output_directory: Optional[str] = None

        self._build_ui()
        self._update_system_stats()
        self._check_initial_setup_recommendation()

    def _build_ui(self):
        # 1. HEADER SUPERIORE
        top_bar = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0, height=70)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # Logo e Titolo
        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20, pady=10)

        title_lbl = ctk.CTkLabel(
            logo_frame,
            text="CONVERTIO DESKTOP",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#e53935"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            logo_frame,
            text="Convertitore Universale Reale: Decodifica & Ricodifica Binaria",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8"
        )
        sub_lbl.pack(anchor="w")

        # Chip di stato dei 4 motori
        engines_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        engines_frame.pack(side="right", padx=20, pady=12)

        self.engine_badges = {}
        badges_info = [
            ("img", "🖼️ Immagini"),
            ("media", "🎬 Audio/Video"),
            ("data", "📊 Dati"),
            ("doc", "📄 Documenti")
        ]
        for key, label in badges_info:
            chip = ctk.CTkLabel(
                engines_frame,
                text=f"{label}: OK ✓",
                fg_color="#1e1e2e",
                text_color="#a6e3a1",
                corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"),
                padx=8,
                pady=4
            )
            chip.pack(side="left", padx=4)
            self.engine_badges[key] = chip

        # Pulsante Gestione Componenti
        setup_btn = ctk.CTkButton(
            engines_frame,
            text="🛠️ Componenti & Portabilità",
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            command=self._open_setup_dialog
        )
        setup_btn.pack(side="left", padx=(10, 0))

        # 2. AREA DI SELEZIONE E DRAG & DROP
        drop_container = ctk.CTkFrame(self, fg_color="transparent")
        drop_container.pack(fill="x", padx=20, pady=(16, 8))

        self.drop_card = ctk.CTkFrame(
            drop_container,
            fg_color="#1e1e2e",
            corner_radius=12,
            border_width=2,
            border_color="#313244",
            cursor="hand2"
        )
        self.drop_card.pack(fill="x", ipady=16)

        # Effetto hover dinamico
        def _on_enter(e):
            self.drop_card.configure(fg_color="#26263a", border_color="#e53935")
        def _on_leave(e):
            self.drop_card.configure(fg_color="#1e1e2e", border_color="#313244")

        self.drop_card.bind("<Enter>", _on_enter)
        self.drop_card.bind("<Leave>", _on_leave)
        self.drop_card.bind("<Button-1>", lambda e: self._choose_files())

        drop_icon = ctk.CTkLabel(self.drop_card, text="📁", font=ctk.CTkFont(size=36))
        drop_icon.pack(pady=(4, 2))
        drop_icon.bind("<Button-1>", lambda e: self._choose_files())

        drop_text = ctk.CTkLabel(
            self.drop_card,
            text="Trascina qui i tuoi file oppure CLICCA PER SELEZIONARLI DAL PC",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        )
        drop_text.pack(pady=2)
        drop_text.bind("<Button-1>", lambda e: self._choose_files())

        drop_sub = ctk.CTkLabel(
            self.drop_card,
            text="Supporta oltre 35 formati: PNG, JPG, WEBP, HEIC, MP4, MKV, MP3, WAV, CSV, XLSX, JSON, PDF, DOCX e molti altri",
            font=ctk.CTkFont(size=11),
            text_color="#89b4fa"
        )
        drop_sub.pack(pady=(0, 4))
        drop_sub.bind("<Button-1>", lambda e: self._choose_files())

        # 3. BARRA DI CONTROLLO BATCH (AZIONI DI GRUPPO)
        batch_bar = ctk.CTkFrame(self, fg_color="#181825", corner_radius=10, height=52)
        batch_bar.pack(fill="x", padx=20, pady=8)
        batch_bar.pack_propagate(False)

        # Destinazione di salvataggio
        dest_frame = ctk.CTkFrame(batch_bar, fg_color="transparent")
        dest_frame.pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(dest_frame, text="Salva in:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))

        self.dest_lbl = ctk.CTkLabel(
            dest_frame,
            text="Stessa cartella sorgente",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
            width=220,
            anchor="w"
        )
        self.dest_lbl.pack(side="left", padx=(0, 6))

        dest_btn = ctk.CTkButton(
            dest_frame,
            text="Sfoglia...",
            width=70,
            height=26,
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(size=11),
            command=self._choose_output_dir
        )
        dest_btn.pack(side="left")

        # Conversione rapida di gruppo
        quick_frame = ctk.CTkFrame(batch_bar, fg_color="transparent")
        quick_frame.pack(side="right", padx=12, pady=10)

        ctk.CTkLabel(quick_frame, text="Tutti in:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))

        self.batch_fmt_menu = ctk.CTkOptionMenu(
            quick_frame,
            values=["MP4", "MP3", "PNG", "JPG", "WEBP", "PDF", "DOCX", "XLSX", "CSV", "JSON"],
            width=90,
            height=28,
            fg_color="#313244",
            button_color="#45475a",
            command=self._apply_batch_format
        )
        self.batch_fmt_menu.set("Seleziona")
        self.batch_fmt_menu.pack(side="left", padx=4)

        # Pulsante Svuota Coda
        clear_btn = ctk.CTkButton(
            quick_frame,
            text="🗑 Svuota",
            width=75,
            height=28,
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(size=11),
            command=self._clear_queue
        )
        clear_btn.pack(side="left", padx=6)

        # Pulsante CONVERTI TUTTI
        self.convert_all_btn = ctk.CTkButton(
            quick_frame,
            text="▶ CONVERTI TUTTI",
            width=140,
            height=28,
            fg_color="#e53935",
            hover_color="#c62828",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._start_batch_conversion
        )
        self.convert_all_btn.pack(side="left", padx=(4, 0))

        # 4. AREA SCROLLABILE CON LE CARD DEI FILE
        self.queue_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.queue_frame.pack(fill="both", expand=True, padx=20, pady=4)

        # Vista vuota segnaposto
        self.empty_placeholder = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
        self.empty_placeholder.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(
            self.empty_placeholder,
            text="Nessun file aggiunto alla coda di conversione.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#6c7086"
        ).pack(pady=4)

        ctk.CTkLabel(
            self.empty_placeholder,
            text="Seleziona uno o più file multimediali, immagini o documenti per iniziare.",
            font=ctk.CTkFont(size=12),
            text_color="#585b70"
        ).pack()

        # 5. FOOTER & BARRA DI STATO DI SISTEMA
        footer_bar = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0, height=36)
        footer_bar.pack(fill="x", side="bottom")
        footer_bar.pack_propagate(False)

        self.summary_lbl = ctk.CTkLabel(
            footer_bar,
            text="0 file in coda",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8"
        )
        self.summary_lbl.pack(side="left", padx=16)

        # Monitoraggio RAM per garantire che l'app sia ultra-leggera
        self.ram_lbl = ctk.CTkLabel(
            footer_bar,
            text="RAM: ~35 MB | CPU: 0%",
            font=ctk.CTkFont(size=11),
            text_color="#89dceb"
        )
        self.ram_lbl.pack(side="right", padx=16)

    def _choose_files(self):
        """Apre il file explorer per selezionare più file contemporaneamente."""
        files = filedialog.askopenfilenames(
            title="Seleziona file da convertire",
            filetypes=[
                ("Tutti i formati supportati", "*.*"),
                ("Immagini", "*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.ico;*.tiff;*.gif;*.heic;*.heif"),
                ("Video & Audio", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.mp3;*.wav;*.flac;*.ogg;*.aac;*.m4a"),
                ("Dati & Tabelle", "*.csv;*.xlsx;*.xls;*.json;*.html;*.xml"),
                ("Documenti", "*.pdf;*.docx;*.txt;*.md")
            ]
        )
        if files:
            self._add_files_to_queue(files)

    def _add_files_to_queue(self, filepaths: List[str]):
        """Aggiunge i percorsi selezionati all'orchestratore e crea le rispettive card grafiche."""
        if self.empty_placeholder and self.empty_placeholder.winfo_exists():
            self.empty_placeholder.pack_forget()

        for fp in filepaths:
            ext = os.path.splitext(fp)[1].lower().lstrip(".")
            targets = get_compatible_targets(ext)
            default_target = targets[0] if targets else "pdf"

            task = self.orchestrator.add_task(fp, default_target, self.output_directory)

            card = FileCard(
                self.queue_frame,
                task,
                on_remove=self._remove_task,
                on_convert_single=self._convert_single
            )
            self.file_cards[task.id] = card

        self._update_queue_summary()

    def _remove_task(self, task_id: str):
        """Rimuove un task dalla coda e distrugge il widget visivo."""
        self.orchestrator.remove_task(task_id)
        if task_id in self.file_cards:
            self.file_cards[task_id].destroy()
            del self.file_cards[task_id]

        if not self.file_cards:
            self.empty_placeholder.pack(fill="both", expand=True, pady=40)

        self._update_queue_summary()

    def _clear_queue(self):
        """Svuota completamente l'elenco."""
        for tid in list(self.file_cards.keys()):
            self._remove_task(tid)

    def _choose_output_dir(self):
        """Permette all'utente di scegliere una cartella di destinazione personalizzata."""
        d = filedialog.askdirectory(title="Seleziona cartella di destinazione")
        if d:
            self.output_directory = d
            display_d = d if len(d) <= 30 else "..." + d[-27:]
            self.dest_lbl.configure(text=display_d, text_color="#ffffff")

            # Aggiorna percorsi di destinazione per i task in coda
            for task in self.orchestrator.tasks.values():
                if task.status == "queued":
                    task.output_dir = d
                    base = os.path.splitext(task.filename)[0]
                    task.dst_path = os.path.join(d, f"{base}.{task.target_ext}")

    def _apply_batch_format(self, target_fmt: str):
        """Applica il formato target a tutti i file compatibili nella coda."""
        t_fmt = target_fmt.lower()
        for task_id, card in self.file_cards.items():
            task = self.orchestrator.tasks.get(task_id)
            if task and task.status == "queued":
                compat = get_compatible_targets(task.src_ext)
                if t_fmt in compat:
                    card.format_menu.set(t_fmt.upper())
                    card._on_format_changed(t_fmt.upper())

    def _convert_single(self, task_id: str):
        """Avvia la conversione di un singolo task."""
        self.orchestrator.start_single(task_id)

    def _start_batch_conversion(self):
        """Avvia la conversione sequenziale di tutta la coda."""
        if not self.orchestrator.tasks:
            messagebox.showinfo("Nessun file", "Aggiungi prima uno o più file alla coda!")
            return

        self.convert_all_btn.configure(text="⏳ In Corso...", state="disabled")
        self.orchestrator.start_batch()

    def _on_task_update_threadsafe(self, task: ConversionTask):
        self.after(0, lambda: self._update_card(task))

    def _update_card(self, task: ConversionTask):
        card = self.file_cards.get(task.id)
        if card:
            card.update_task_ui()
        self._update_queue_summary()

    def _on_task_complete_threadsafe(self, task: ConversionTask):
        self.after(0, lambda: self._on_task_complete(task))

    def _on_task_complete(self, task: ConversionTask):
        self._update_card(task)

    def _on_all_completed_threadsafe(self):
        self.after(0, self._on_all_completed)

    def _on_all_completed(self):
        self.convert_all_btn.configure(text="▶ CONVERTI TUTTI", state="normal")
        self._update_queue_summary()
        messagebox.showinfo("Conversione Terminata", "Tutti i file in coda sono stati convertiti con successo!")

    def _update_queue_summary(self):
        total = len(self.orchestrator.tasks)
        completed = sum(1 for t in self.orchestrator.tasks.values() if t.status == "completed")
        running = sum(1 for t in self.orchestrator.tasks.values() if t.status == "running")

        if total == 0:
            self.summary_lbl.configure(text="0 file in coda")
        else:
            self.summary_lbl.configure(text=f"{total} file totali | {completed} completati | {running} in elaborazione")

    def _update_system_stats(self):
        """Aggiorna le statistiche di utilizzo memoria per attestare la leggerezza."""
        try:
            proc = psutil.Process()
            mem_mb = proc.memory_info().rss / (1024 * 1024)
            cpu_pct = proc.cpu_percent()
            self.ram_lbl.configure(text=f"RAM: ~{mem_mb:.1f} MB | CPU: {cpu_pct:.0f}%")
        except Exception:
            pass
        self.after(2500, self._update_system_stats)

    def _open_setup_dialog(self):
        """Apre la finestra di configurazione portatile e verifica dipendenze."""
        SetupDialog(self, on_complete=self._refresh_engine_chips)

    def _refresh_engine_chips(self):
        """Aggiorna i chip di stato nell'header."""
        comps = {c["id"]: c["installed"] for c in check_all_components()}

        # Immagini
        img_ok = comps.get("pillow", False)
        self.engine_badges["img"].configure(
            text=f"🖼️ Immagini: {'OK ✓' if img_ok else 'Mancante ✕'}",
            text_color="#a6e3a1" if img_ok else "#f38ba8"
        )

        # Audio/Video
        media_ok = is_ffmpeg_available()
        self.engine_badges["media"].configure(
            text=f"🎬 Audio/Video: {'OK ✓' if media_ok else 'Mancante ✕'}",
            text_color="#a6e3a1" if media_ok else "#f38ba8"
        )

        # Dati
        data_ok = comps.get("pandas", False)
        self.engine_badges["data"].configure(
            text=f"📊 Dati: {'OK ✓' if data_ok else 'Base'}",
            text_color="#a6e3a1" if data_ok else "#fab387"
        )

        # Documenti
        doc_ok = comps.get("pdf2docx", False) and comps.get("pymupdf", False)
        self.engine_badges["doc"].configure(
            text=f"📄 Documenti: {'OK ✓' if doc_ok else 'Parziale'}",
            text_color="#a6e3a1" if doc_ok else "#fab387"
        )

    def _check_initial_setup_recommendation(self):
        self._refresh_engine_chips()
        comps = check_all_components()
        missing = [c["name"] for c in comps if not c["installed"]]
        if missing:
            # Notifica visiva gentile non bloccante
            pass


def launch():
    app = UniversalConverterApp()
    app.mainloop()

if __name__ == "__main__":
    launch()
