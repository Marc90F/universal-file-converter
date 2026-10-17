"""
Finestra modale delle opzioni di conversione personalizzate.
Permette di regolare qualità, bitrate, risoluzione e parametri specifici per formato.
"""

import customtkinter as ctk
from typing import Dict, Any, Callable
from core.format_registry import get_category, CATEGORY_IMAGE, CATEGORY_VIDEO, CATEGORY_AUDIO, CATEGORY_DATA, CATEGORY_DOCUMENT

class OptionsModal(ctk.CTkToplevel):
    def __init__(self, parent, filename: str, src_ext: str, dst_ext: str, current_options: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)

        self.title(f"Opzioni di Conversione - {filename}")
        self.geometry("520x460")
        self.minsize(480, 400)
        self.attributes("-topmost", True)
        self.transient(parent)
        self.grab_set()

        self.src_ext = src_ext.lower().lstrip(".")
        self.dst_ext = dst_ext.lower().lstrip(".")
        self.category = get_category(self.src_ext)
        self.options = dict(current_options)
        self.on_save = on_save

        # Intestazione
        head = ctk.CTkFrame(self, fg_color="#1e1e2e", corner_radius=10)
        head.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            head,
            text=f"Parametri di Codifica: {self.src_ext.upper()} ➔ {self.dst_ext.upper()}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#ffffff"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            head,
            text=f"File: {filename}",
            font=ctk.CTkFont(size=11),
            text_color="#a6adc8"
        ).pack(anchor="w", padx=14, pady=(0, 10))

        # Contenitore opzioni
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=6)

        # 1. OPZIONI IMMAGINE
        if self.category == CATEGORY_IMAGE or self.dst_ext in ("jpg", "jpeg", "webp", "png"):
            # Slider Qualità
            q_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
            q_frame.pack(fill="x", pady=6)

            ctk.CTkLabel(q_frame, text="Livello di Compressione / Qualità:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 2))

            q_val = self.options.get("quality", 95)
            self.q_lbl = ctk.CTkLabel(q_frame, text=f"{q_val}%", font=ctk.CTkFont(size=12))
            self.q_lbl.pack(anchor="e", padx=12)

            self.q_slider = ctk.CTkSlider(
                q_frame,
                from_=10,
                to=100,
                number_of_steps=90,
                command=self._on_quality_change
            )
            self.q_slider.set(q_val)
            self.q_slider.pack(fill="x", padx=12, pady=(0, 12))

            # Risoluzione
            res_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
            res_frame.pack(fill="x", pady=6)

            ctk.CTkLabel(res_frame, text="Ridimensionamento:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
            self.img_res_menu = ctk.CTkOptionMenu(
                res_frame,
                values=["Originale", "1920x1080 (Full HD)", "1280x720 (HD)", "800x600", "512x512", "256x256"]
            )
            self.img_res_menu.set(self.options.get("img_res_preset", "Originale"))
            self.img_res_menu.pack(fill="x", padx=12, pady=(0, 12))

        # 2. OPZIONI VIDEO & AUDIO
        if self.category in (CATEGORY_VIDEO, CATEGORY_AUDIO) or self.dst_ext in ("mp4", "mkv", "avi", "mov", "mp3", "wav", "aac", "flac"):
            # Bitrate Audio
            ab_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
            ab_frame.pack(fill="x", pady=6)

            ctk.CTkLabel(ab_frame, text="Bitrate Audio Target:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
            self.audio_br_menu = ctk.CTkOptionMenu(
                ab_frame,
                values=["128k (Standard)", "192k (Alta)", "256k (Molto Alta)", "320k (Massima Fedeltà)"]
            )
            cur_br = self.options.get("audio_bitrate", "192k")
            for v in self.audio_br_menu._values:
                if cur_br in v:
                    self.audio_br_menu.set(v)
                    break
            self.audio_br_menu.pack(fill="x", padx=12, pady=(0, 12))

            if self.category == CATEGORY_VIDEO and self.dst_ext in ("mp4", "mkv", "avi", "mov", "webm"):
                # Qualità Video CRF
                vq_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
                vq_frame.pack(fill="x", pady=6)

                ctk.CTkLabel(vq_frame, text="Profilo Qualità Video (CRF):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
                self.vq_menu = ctk.CTkOptionMenu(
                    vq_frame,
                    values=["Alta Qualità (CRF 18)", "Bilanciata (CRF 23)", "Compressione Massima (CRF 28)"]
                )
                self.vq_menu.set("Bilanciata (CRF 23)")
                self.vq_menu.pack(fill="x", padx=12, pady=(0, 12))

                # Risoluzione Video
                vr_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
                vr_frame.pack(fill="x", pady=6)

                ctk.CTkLabel(vr_frame, text="Risoluzione Video:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
                self.vr_menu = ctk.CTkOptionMenu(
                    vr_frame,
                    values=["Originale", "1080p (Full HD)", "720p (HD)", "480p (SD)"]
                )
                self.vr_menu.set(self.options.get("resolution", "original").capitalize() if self.options.get("resolution") != "original" else "Originale")
                self.vr_menu.pack(fill="x", padx=12, pady=(0, 12))

        # 3. OPZIONI DATI E TABELLE
        if self.category == CATEGORY_DATA or self.dst_ext in ("csv", "xlsx", "json"):
            data_frame = ctk.CTkFrame(body, fg_color="#181825", corner_radius=8)
            data_frame.pack(fill="x", pady=6)

            ctk.CTkLabel(data_frame, text="Opzioni Esportazione Dati:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))

            ctk.CTkLabel(data_frame, text="Codifica e Integrità:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12)
            ctk.CTkLabel(
                data_frame,
                text="Salvataggio automatico in UTF-8 con supporto caratteri speciali ed emoji.",
                text_color="#a6adc8",
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", padx=12, pady=(0, 12))

        # Footer con pulsanti Salva / Annulla
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Applica Opzioni",
            fg_color="#e53935",
            hover_color="#c62828",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_and_close
        )
        save_btn.pack(side="right", padx=(8, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Annulla",
            fg_color="#313244",
            hover_color="#45475a",
            command=self.destroy
        )
        cancel_btn.pack(side="right")

    def _on_quality_change(self, val):
        self.q_lbl.configure(text=f"{int(val)}%")

    def _save_and_close(self):
        new_opts = dict(self.options)

        # Salva qualità
        if hasattr(self, "q_slider"):
            new_opts["quality"] = int(self.q_slider.get())

        # Salva risoluzione immagine
        if hasattr(self, "img_res_menu"):
            preset = self.img_res_menu.get()
            new_opts["img_res_preset"] = preset
            if "1920x1080" in preset:
                new_opts["resize"] = (1920, 1080)
            elif "1280x720" in preset:
                new_opts["resize"] = (1280, 720)
            elif "800x600" in preset:
                new_opts["resize"] = (800, 600)
            elif "512x512" in preset:
                new_opts["resize"] = (512, 512)
            elif "256x256" in preset:
                new_opts["resize"] = (256, 256)
            else:
                new_opts["resize"] = None

        # Salva bitrate audio
        if hasattr(self, "audio_br_menu"):
            br_str = self.audio_br_menu.get()
            if "128k" in br_str:
                new_opts["audio_bitrate"] = "128k"
            elif "256k" in br_str:
                new_opts["audio_bitrate"] = "256k"
            elif "320k" in br_str:
                new_opts["audio_bitrate"] = "320k"
            else:
                new_opts["audio_bitrate"] = "192k"

        # Salva qualità video CRF
        if hasattr(self, "vq_menu"):
            vq_str = self.vq_menu.get()
            if "Alta" in vq_str:
                new_opts["video_quality"] = "high"
            elif "Massima" in vq_str:
                new_opts["video_quality"] = "low"
            else:
                new_opts["video_quality"] = "medium"

        # Salva risoluzione video
        if hasattr(self, "vr_menu"):
            vr_str = self.vr_menu.get()
            if "1080p" in vr_str:
                new_opts["resolution"] = "1080p"
            elif "720p" in vr_str:
                new_opts["resolution"] = "720p"
            elif "480p" in vr_str:
                new_opts["resolution"] = "480p"
            else:
                new_opts["resolution"] = "original"

        self.on_save(new_opts)
        self.destroy()
