"""
Finestra modale esplicativa e guidata.
Spiega in dettaglio cosa avviene 'sotto il cofano' a livello binario durante la conversione,
rendendo evidente la differenza tra una vera conversione e una semplice rinomina dell'estensione.
"""

import customtkinter as ctk
from core.format_registry import get_explanation

class ExplainModal(ctk.CTkToplevel):
    def __init__(self, parent, src_ext: str, dst_ext: str):
        super().__init__(parent)

        self.title("Dettaglio Tecnico di Conversione - Sotto il Cofano")
        self.geometry("640x520")
        self.minsize(550, 450)
        self.attributes("-topmost", True)

        # Centra la finestra rispetto al genitore
        self.transient(parent)
        self.grab_set()

        info = get_explanation(src_ext, dst_ext)

        # Header Frame
        header_frame = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=12)
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=info["title"],
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 4))

        meta_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        meta_frame.pack(fill="x", padx=16, pady=(0, 12))

        cat_badge = ctk.CTkLabel(
            meta_frame,
            text=f"CATEGORIA: {info['category'].upper()}",
            fg_color="#313244",
            text_color="#89b4fa",
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            padx=8,
            pady=3
        )
        cat_badge.pack(side="left", padx=(0, 8))

        engine_badge = ctk.CTkLabel(
            meta_frame,
            text=f"MOTORE REALE: {info['engine']}",
            fg_color="#313244",
            text_color="#a6e3a1",
            corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            padx=8,
            pady=3
        )
        engine_badge.pack(side="left")

        # Scrollable Content Frame
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Sezione 1: Cosa avviene realmente
        section1 = ctk.CTkFrame(scroll_frame, fg_color="#181825", corner_radius=10)
        section1.pack(fill="x", pady=6)

        sec1_header = ctk.CTkLabel(
            section1,
            text="🔬 COSA AVVIENE REALMENTE SOTTO IL COFANO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#fab387"
        )
        sec1_header.pack(anchor="w", padx=14, pady=(10, 4))

        sec1_body = ctk.CTkLabel(
            section1,
            text=info["how_it_works"],
            font=ctk.CTkFont(size=12),
            text_color="#cdd6f4",
            wraplength=560,
            justify="left"
        )
        sec1_body.pack(anchor="w", padx=14, pady=(0, 12))

        # Sezione 2: Perché non basta rinominare
        section2 = ctk.CTkFrame(scroll_frame, fg_color="#181825", corner_radius=10)
        section2.pack(fill="x", pady=6)

        sec2_header = ctk.CTkLabel(
            section2,
            text="⚠️ PERCHÉ UNA SEMPLICE RINOMINA DELL'ESTENSIONE FALLISCE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f38ba8"
        )
        sec2_header.pack(anchor="w", padx=14, pady=(10, 4))

        sec2_body = ctk.CTkLabel(
            section2,
            text=info["why_not_rename"],
            font=ctk.CTkFont(size=12),
            text_color="#cdd6f4",
            wraplength=560,
            justify="left"
        )
        sec2_body.pack(anchor="w", padx=14, pady=(0, 12))

        # Sezione 3: Pipeline binaria
        section3 = ctk.CTkFrame(scroll_frame, fg_color="#181825", corner_radius=10)
        section3.pack(fill="x", pady=6)

        sec3_header = ctk.CTkLabel(
            section3,
            text="🔄 FLUSSO DELLA PIPELINE DI CONVERSIONE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#89dceb"
        )
        sec3_header.pack(anchor="w", padx=14, pady=(10, 6))

        pipeline_steps = [
            f"1. Lettura header binario del file sorgente ({src_ext.upper()}) e verifica integrità.",
            "2. Decodifica dei flussi compressi nella rappresentazione grezza non compressa in RAM.",
            "3. Applicazione delle trasformazioni di layout, canali cromatici, tabelle o campioni PCM.",
            f"4. Ricodifica nel contenitore di arrivo ({dst_ext.upper()}) con serializzazione conforme agli standard.",
            "5. Scrittura del nuovo flusso binario su disco con verifica di checksum."
        ]
        for step in pipeline_steps:
            step_lbl = ctk.CTkLabel(
                section3,
                text=step,
                font=ctk.CTkFont(size=11),
                text_color="#a6adc8",
                wraplength=560,
                justify="left"
            )
            step_lbl.pack(anchor="w", padx=14, pady=2)

        ctk.CTkLabel(section3, text="").pack(pady=4)

        # Pulsante di chiusura
        close_btn = ctk.CTkButton(
            self,
            text="Ho Capito",
            fg_color="#e53935",
            hover_color="#c62828",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy
        )
        close_btn.pack(fill="x", padx=16, pady=12)
