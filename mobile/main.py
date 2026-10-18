"""
Universal File Converter — Android Edition
Interfaccia touch moderna per smartphone Android sviluppata con Kivy.
Ottimizzata per schermi touch, permessi Android Scoped Storage e gestione asincrona multithread.
"""

import os
import sys
import threading
from typing import List, Dict, Any, Optional

# Kivy Configuration
os.environ["KIVY_NO_CONSOLELOG"] = "0"
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

# Imposta background scuro coerente con il design desktop
Window.clearcolor = (0.04, 0.04, 0.06, 1.0) # #0a0a10

# Aggiungi cartella superiore al path per condividere core e engines
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from core.format_registry import get_category, get_compatible_targets, get_explanation, CATEGORY_ICONS
from core.orchestrator import ConversionOrchestrator, ConversionTask

class ExplainPopup(Popup):
    def __init__(self, src_ext: str, dst_ext: str, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Come Funziona: {src_ext.upper()} -> {dst_ext.upper()}"
        self.size_hint = (0.9, 0.7)
        self.auto_dismiss = True

        info = get_explanation(src_ext, dst_ext)

        layout = BoxLayout(orientation="vertical", padding=16, spacing=12)

        cat_lbl = Label(
            text=f"[b]CATEGORIA:[/b] {info['category'].upper()}",
            markup=True,
            color=(0.54, 0.86, 0.92, 1),
            size_hint_y=None,
            height=30
        )
        layout.add_widget(cat_lbl)

        eng_lbl = Label(
            text=f"[b]MOTORE REALE:[/b] {info['engine']}",
            markup=True,
            color=(0.65, 0.89, 0.63, 1),
            size_hint_y=None,
            height=30
        )
        layout.add_widget(eng_lbl)

        scroll = ScrollView(size_hint=(1, 1))
        desc_lbl = Label(
            text=info["how_it_works"] + "\n\n" + info["why_not_rename"],
            color=(0.8, 0.84, 0.96, 1),
            text_size=(Window.width * 0.8, None),
            valign="top"
        )
        desc_lbl.bind(texture_size=desc_lbl.setter('size'))
        scroll.add_widget(desc_lbl)
        layout.add_widget(scroll)

        close_btn = Button(
            text="Ho Capito",
            background_color=(0.9, 0.22, 0.21, 1),
            size_hint_y=None,
            height=46
        )
        close_btn.bind(on_release=self.dismiss)
        layout.add_widget(close_btn)

        self.content = layout


class MobileFileCard(BoxLayout):
    def __init__(self, task: ConversionTask, on_convert_cb, on_remove_cb, **kwargs):
        super().__init__(orientation="vertical", padding=12, spacing=8, size_hint_y=None, height=140, **kwargs)
        self.task = task
        self.on_convert_cb = on_convert_cb
        self.on_remove_cb = on_remove_cb

        # Riga 1: Icona, Nome file e pulsante rimozione
        row1 = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=36)
        cat_icon = CATEGORY_ICONS.get(task.category, "📁")
        row1.add_widget(Label(text=cat_icon, font_size="20sp", size_hint_x=None, width=32))

        disp_name = task.filename if len(task.filename) <= 20 else task.filename[:17] + "..."
        row1.add_widget(Label(text=f"[b]{disp_name}[/b]", markup=True, halign="left", text_size=(200, None)))

        del_btn = Button(text="✕", size_hint_x=None, width=36, background_color=(0.2, 0.2, 0.28, 1))
        del_btn.bind(on_release=lambda x: self.on_remove_cb(self.task.id))
        row1.add_widget(del_btn)
        self.add_widget(row1)

        # Riga 2: Formato target, pulsante info e converti
        row2 = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=38)
        row2.add_widget(Label(text="in", size_hint_x=None, width=24, color=(0.65, 0.68, 0.78, 1)))

        compat = get_compatible_targets(task.src_ext)
        if not compat:
            compat = [task.target_ext]
        self.spinner = Spinner(
            text=task.target_ext.upper(),
            values=[t.upper() for t in compat],
            size_hint_x=0.4,
            background_color=(0.2, 0.2, 0.28, 1)
        )
        self.spinner.bind(text=self._on_format_change)
        row2.add_widget(self.spinner)

        info_btn = Button(text="💡 Info", size_hint_x=0.3, background_color=(0.17, 0.18, 0.26, 1))
        info_btn.bind(on_release=lambda x: ExplainPopup(self.task.src_ext, self.task.target_ext).open())
        row2.add_widget(info_btn)

        self.action_btn = Button(text="▶", size_hint_x=0.25, background_color=(0.9, 0.22, 0.21, 1))
        self.action_btn.bind(on_release=lambda x: self.on_convert_cb(self.task.id))
        row2.add_widget(self.action_btn)
        self.add_widget(row2)

        # Riga 3: Barra di progresso e stato
        self.pbar = ProgressBar(max=100, value=0, size_hint_y=None, height=8)
        self.add_widget(self.pbar)

        self.status_lbl = Label(
            text="Pronto per la conversione",
            font_size="11sp",
            color=(0.65, 0.68, 0.78, 1),
            size_hint_y=None,
            height=20
        )
        self.add_widget(self.status_lbl)

    def _on_format_change(self, spinner, text):
        self.task.target_ext = text.lower()
        base = os.path.splitext(self.task.filename)[0]
        self.task.dst_path = os.path.join(self.task.output_dir, f"{base}.{self.task.target_ext}")

    def update_ui(self):
        self.pbar.value = self.task.progress
        if self.task.status == "running":
            self.status_lbl.text = f"{self.task.progress}% - {self.task.status_message}"
            self.action_btn.text = "⏳"
            self.action_btn.disabled = True
        elif self.task.status == "completed":
            self.status_lbl.text = "Completato 100% ✓"
            self.action_btn.text = "✓"
            self.action_btn.background_color = (0.1, 0.72, 0.5, 1)
            self.action_btn.disabled = True
        elif self.task.status == "error":
            self.status_lbl.text = f"Errore: {self.task.error_message[:30]}"
            self.action_btn.text = "↻"
            self.action_btn.disabled = False


class UniversalConverterMobileApp(App):
    def build(self):
        self.title = "Universal File Converter"
        self.orchestrator = ConversionOrchestrator()
        self.orchestrator.on_task_update = self._on_task_update_threadsafe
        self.orchestrator.on_all_completed = self._on_all_completed_threadsafe
        self.cards = {}

        # Richiedi permessi Android se su dispositivo mobile reale
        self._request_android_permissions()

        # Layout Principale
        root = BoxLayout(orientation="vertical", padding=16, spacing=14)

        # Header Mobile
        hdr = BoxLayout(orientation="vertical", size_hint_y=None, height=64, spacing=2)
        title_lbl = Label(text="[b]UNIVERSAL FILE CONVERTER[/b]", markup=True, font_size="18sp", color=(0.9, 0.22, 0.21, 1))
        sub_lbl = Label(text="Mobile Edition • Decodifica & Ricodifica Reale", font_size="11sp", color=(0.6, 0.65, 0.75, 1))
        hdr.add_widget(title_lbl)
        hdr.add_widget(sub_lbl)
        root.add_widget(hdr)

        # Pulsante Seleziona File Mobile
        pick_btn = Button(
            text="📂 TOCCA PER SELEZIONARE FILE DAL DISPOSITIVO",
            font_size="13sp",
            bold=True,
            background_color=(0.12, 0.12, 0.18, 1),
            size_hint_y=None,
            height=54
        )
        pick_btn.bind(on_release=self._open_file_chooser)
        root.add_widget(pick_btn)

        # Area di scorrimento card dei file
        self.scroll = ScrollView(size_hint=(1, 1))
        self.card_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.card_container.bind(minimum_height=self.card_container.setter('height'))
        self.scroll.add_widget(self.card_container)
        root.add_widget(self.scroll)

        # Footer con pulsante CONVERTI TUTTI
        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=48, spacing=10)
        self.summary_lbl = Label(text="0 file in coda", font_size="12sp", color=(0.6, 0.65, 0.75, 1))
        footer.add_widget(self.summary_lbl)

        self.convert_all_btn = Button(
            text="▶ CONVERTI TUTTI",
            bold=True,
            background_color=(0.9, 0.22, 0.21, 1),
            size_hint_x=0.55
        )
        self.convert_all_btn.bind(on_release=lambda x: self._convert_all())
        footer.add_widget(self.convert_all_btn)
        root.add_widget(footer)

        return root

    def _request_android_permissions(self):
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.INTERNET
                ])
            except Exception:
                pass

    def _open_file_chooser(self, instance):
        # Percorso di partenza predefinito su Android o desktop
        start_path = "/storage/emulated/0" if platform == "android" and os.path.exists("/storage/emulated/0") else os.path.expanduser("~")

        box = BoxLayout(orientation="vertical", spacing=8, padding=10)
        fc = FileChooserListView(path=start_path, multiselect=True)
        box.add_widget(fc)

        btn_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=44, spacing=10)
        select_btn = Button(text="Conferma Selezione", background_color=(0.9, 0.22, 0.21, 1))
        cancel_btn = Button(text="Annulla", background_color=(0.2, 0.2, 0.28, 1))
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(select_btn)
        box.add_widget(btn_box)

        popup = Popup(title="Seleziona i file da convertire", content=box, size_hint=(0.95, 0.9))

        def _on_select(x):
            if fc.selection:
                self._add_files(fc.selection)
            popup.dismiss()

        select_btn.bind(on_release=_on_select)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _add_files(self, paths: List[str]):
        # Su Android salva nella cartella Download o nella stessa cartella
        out_dir = "/storage/emulated/0/Download" if platform == "android" and os.path.exists("/storage/emulated/0/Download") else None

        for p in paths:
            ext = os.path.splitext(p)[1].lower().lstrip(".")
            targets = get_compatible_targets(ext)
            target = targets[0] if targets else "pdf"

            task = self.orchestrator.add_task(p, target, output_dir=out_dir)
            card = MobileFileCard(task, on_convert_cb=self._convert_single, on_remove_cb=self._remove_task)
            self.cards[task.id] = card
            self.card_container.add_widget(card)

        self._update_summary()

    def _remove_task(self, task_id: str):
        self.orchestrator.remove_task(task_id)
        if task_id in self.cards:
            self.card_container.remove_widget(self.cards[task_id])
            del self.cards[task_id]
        self._update_summary()

    def _convert_single(self, task_id: str):
        self.orchestrator.start_single(task_id)

    def _convert_all(self):
        if not self.orchestrator.tasks:
            return
        self.convert_all_btn.text = "In corso..."
        self.convert_all_btn.disabled = True
        self.orchestrator.start_batch()

    def _on_task_update_threadsafe(self, task: ConversionTask):
        Clock.schedule_once(lambda dt: self._update_card(task))

    def _update_card(self, task: ConversionTask):
        card = self.cards.get(task.id)
        if card:
            card.update_ui()
        self._update_summary()

    def _on_all_completed_threadsafe(self):
        Clock.schedule_once(lambda dt: self._all_done())

    def _all_done(self):
        self.convert_all_btn.text = "▶ CONVERTI TUTTI"
        self.convert_all_btn.disabled = False
        popup = Popup(
            title="Completato",
            content=Label(text="Tutti i file sono stati convertiti con successo!"),
            size_hint=(0.8, 0.3)
        )
        popup.open()

    def _update_summary(self):
        tot = len(self.orchestrator.tasks)
        done = sum(1 for t in self.orchestrator.tasks.values() if t.status == "completed")
        self.summary_lbl.text = f"{tot} file in coda ({done} completati)"


if __name__ == "__main__":
    UniversalConverterMobileApp().run()
