"""
Widget grafico del singolo file card in coda stile Convertio.
Presenta icona, nome, dimensione, selettore di formato target, pulsante esplicativo
'Come Funziona Sotto Il Cofano', opzioni e barra di progresso dinamica.
"""

import os
import subprocess
import customtkinter as ctk
from typing import Callable, Optional
from core.orchestrator import ConversionTask
from core.format_registry import get_category, get_compatible_targets, CATEGORY_ICONS
from gui.explain_modal import ExplainModal
from gui.options_modal import OptionsModal

def format_size(bytes_num: int) -> str:
    """Formatta i byte in unità umane leggibili (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

class FileCard(ctk.CTkFrame):
    def __init__(self, parent, task: ConversionTask, on_remove: Callable[[str], None], on_convert_single: Callable[[str], None]):
        super().__init__(parent, fg_color="#181825", corner_radius=10)
        self.task = task
        self.on_remove = on_remove
        self.on_convert_single = on_convert_single

        self.pack(fill="x", padx=8, pady=4)

        # Riga 1: Dati principali del file
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 4))

        # Icona di categoria
        cat_icon = CATEGORY_ICONS.get(task.category, "📁")
        self.icon_lbl = ctk.CTkLabel(row1, text=cat_icon, font=ctk.CTkFont(size=20))
        self.icon_lbl.pack(side="left", padx=(0, 8))

        # Nome file e dimensione
        name_frame = ctk.CTkFrame(row1, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)

        display_name = task.filename if len(task.filename) <= 35 else task.filename[:32] + "..."
        self.name_lbl = ctk.CTkLabel(
            name_frame,
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ffffff",
            anchor="w"
        )
        self.name_lbl.pack(anchor="w")

        size_bytes = os.path.getsize(task.src_path) if os.path.exists(task.src_path) else 0
        self.size_lbl = ctk.CTkLabel(
            name_frame,
            text=f"{format_size(size_bytes)}  •  {task.category}",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
            anchor="w"
        )
        self.size_lbl.pack(anchor="w")

        # Controlli lato destro (Dropdown formato target, Opzioni, Come Funziona, Rimuovi)
        right_controls = ctk.CTkFrame(row1, fg_color="transparent")
        right_controls.pack(side="right")

        # Etichetta "in"
        ctk.CTkLabel(right_controls, text="in", font=ctk.CTkFont(size=12), text_color="#a6adc8").pack(side="left", padx=4)

        # Dropdown formati compatibili
        compat_targets = get_compatible_targets(task.src_ext)
        if not compat_targets:
            compat_targets = [task.target_ext]
        if task.target_ext not in compat_targets:
            compat_targets.insert(0, task.target_ext)

        self.format_menu = ctk.CTkOptionMenu(
            right_controls,
            values=[t.upper() for t in compat_targets],
            width=90,
            height=28,
            fg_color="#313244",
            button_color="#45475a",
            button_hover_color="#585b70",
            command=self._on_format_changed
        )
        self.format_menu.set(task.target_ext.upper())
        self.format_menu.pack(side="left", padx=6)

        # Pulsante "Come Funziona" (Esplicativo e guidato)
        self.explain_btn = ctk.CTkButton(
            right_controls,
            text="💡 Come Funziona",
            width=110,
            height=28,
            fg_color="#2b2d42",
            hover_color="#3d405b",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#89dceb",
            command=self._open_explain_modal
        )
        self.explain_btn.pack(side="left", padx=4)

        # Pulsante Opzioni
        self.opt_btn = ctk.CTkButton(
            right_controls,
            text="⚙ Opzioni",
            width=75,
            height=28,
            fg_color="#2b2d42",
            hover_color="#3d405b",
            font=ctk.CTkFont(size=11),
            command=self._open_options_modal
        )
        self.opt_btn.pack(side="left", padx=4)

        # Pulsante Converti Singolo
        self.action_btn = ctk.CTkButton(
            right_controls,
            text="▶",
            width=32,
            height=28,
            fg_color="#e53935",
            hover_color="#c62828",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_action_click
        )
        self.action_btn.pack(side="left", padx=4)

        # Pulsante Rimuovi
        self.del_btn = ctk.CTkButton(
            right_controls,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#f38ba8",
            text_color="#a6adc8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.on_remove(task.id)
        )
        self.del_btn.pack(side="left", padx=(4, 0))

        # Riga 2: Barra di avanzamento e stato
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(0, 10))

        self.prog_bar = ctk.CTkProgressBar(row2, height=6, fg_color="#313244", progress_color="#e53935")
        self.prog_bar.set(0)
        self.prog_bar.pack(fill="x", side="left", expand=True, padx=(0, 10))

        self.status_lbl = ctk.CTkLabel(
            row2,
            text="Pronto per la conversione",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8",
            width=200,
            anchor="e"
        )
        self.status_lbl.pack(side="right")

    def _on_format_changed(self, new_fmt: str):
        self.task.target_ext = new_fmt.lower()
        base = os.path.splitext(self.task.filename)[0]
        self.task.dst_path = os.path.join(self.task.output_dir, f"{base}.{self.task.target_ext}")

    def _open_explain_modal(self):
        ExplainModal(self.winfo_toplevel(), self.task.src_ext, self.task.target_ext)

    def _open_options_modal(self):
        OptionsModal(
            self.winfo_toplevel(),
            self.task.filename,
            self.task.src_ext,
            self.task.target_ext,
            self.task.options,
            self._save_options
        )

    def _save_options(self, new_opts):
        self.task.options.update(new_opts)

    def _on_action_click(self):
        if self.task.status == "completed":
            # Apri cartella o seleziona file in modo sicuro (senza shell) su Windows, macOS e Linux
            abs_dst = os.path.abspath(self.task.dst_path)
            out_dir = os.path.dirname(abs_dst)

            if sys.platform == "darwin": # macOS Finder
                if os.path.exists(abs_dst):
                    subprocess.Popen(["open", "-R", abs_dst])
                else:
                    subprocess.Popen(["open", out_dir])
            elif sys.platform.startswith("linux"): # Linux X11/Wayland
                subprocess.Popen(["xdg-open", out_dir])
            else: # Windows Explorer
                if os.path.exists(abs_dst):
                    subprocess.Popen(["explorer", f"/select,{abs_dst}"])
                else:
                    subprocess.Popen(["explorer", out_dir])
        elif self.task.status in ("queued", "error"):
            self.on_convert_single(self.task.id)

    def update_task_ui(self):
        """Aggiorna lo stato visivo in base al task corrente."""
        pct = self.task.progress / 100.0
        self.prog_bar.set(pct)

        if self.task.status == "queued":
            self.prog_bar.configure(progress_color="#e53935")
            self.status_lbl.configure(text=self.task.status_message, text_color="#a6adc8")
            self.action_btn.configure(text="▶", state="normal", fg_color="#e53935")

        elif self.task.status == "running":
            self.prog_bar.configure(progress_color="#fab387")
            self.status_lbl.configure(text=f"{self.task.progress}% - {self.task.status_message}", text_color="#fab387")
            self.action_btn.configure(text="⏳", state="disabled")
            self.format_menu.configure(state="disabled")

        elif self.task.status == "completed":
            self.prog_bar.configure(progress_color="#a6e3a1")
            ratio = self.task.stats.get("compression_ratio", "")
            elapsed = self.task.stats.get("elapsed_sec", "")
            extra_info = f" ({ratio})" if ratio else f" ({elapsed})" if elapsed else ""
            self.status_lbl.configure(text=f"Completato 100%{extra_info}", text_color="#a6e3a1")
            self.action_btn.configure(text="📁", state="normal", fg_color="#2e7d32", hover_color="#1b5e20")
            self.format_menu.configure(state="disabled")

        elif self.task.status == "error":
            self.prog_bar.configure(progress_color="#f38ba8")
            self.status_lbl.configure(text=self.task.status_message, text_color="#f38ba8")
            self.action_btn.configure(text="↻", state="normal", fg_color="#c62828")
            self.format_menu.configure(state="normal")
