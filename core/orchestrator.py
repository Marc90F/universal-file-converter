"""
Orchestratore centrale del Convertitore Universale.
Gestisce l'accodamento dei file, l'ispezione dei tipi MIME, l'assegnazione
al motore di decodifica/ricodifica corretto e l'esecuzione asincrona su thread separati.
"""

import os
import time
import uuid
import threading
from typing import Dict, List, Any, Callable, Optional
from core.format_registry import get_category, CATEGORY_IMAGE, CATEGORY_VIDEO, CATEGORY_AUDIO, CATEGORY_DATA, CATEGORY_DOCUMENT
from engines.image_engine import convert_image
from engines.media_engine import convert_media
from engines.data_engine import convert_data
from engines.doc_engine import convert_document

class ConversionTask:
    def __init__(self, src_path: str, target_ext: str, output_dir: Optional[str] = None, options: Optional[Dict[str, Any]] = None):
        self.id = str(uuid.uuid4())[:8]
        self.src_path = src_path
        self.filename = os.path.basename(src_path)
        self.src_ext = os.path.splitext(src_path)[1].lower().lstrip(".")
        self.target_ext = "".join(c for c in target_ext.lower().lstrip(".") if c.isalnum() or c in ("-", "_"))
        self.category = get_category(self.src_ext)

        self.output_dir = output_dir or os.path.dirname(src_path)
        base_name = os.path.splitext(self.filename)[0]
        
        # Protezione anti-sovrascrittura: se sorgente e destinazione coincidono, aggiunge '_converted'
        candidate_dst = os.path.join(self.output_dir, f"{base_name}.{self.target_ext}")
        if os.path.abspath(candidate_dst) == os.path.abspath(self.src_path):
            candidate_dst = os.path.join(self.output_dir, f"{base_name}_converted.{self.target_ext}")
        self.dst_path = candidate_dst

        self.options = options or {}
        self.status = "queued" # queued, running, completed, error, cancelled
        self.progress = 0
        self.status_message = "In attesa..."
        self.error_message = ""
        self.stats = {}
        self.cancelled = False

    def is_cancelled(self) -> bool:
        return self.cancelled

    def cancel(self):
        self.cancelled = True
        self.status = "cancelled"
        self.status_message = "Annullato dall'utente"


class ConversionOrchestrator:
    def __init__(self):
        self.tasks: Dict[str, ConversionTask] = {}
        self.lock = threading.Lock()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Callbacks per la UI
        self.on_task_update: Optional[Callable[[ConversionTask], None]] = None
        self.on_task_complete: Optional[Callable[[ConversionTask], None]] = None
        self.on_task_error: Optional[Callable[[ConversionTask, str], None]] = None
        self.on_all_completed: Optional[Callable[[], None]] = None

    def add_task(self, src_path: str, target_ext: str, output_dir: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> ConversionTask:
        with self.lock:
            task = ConversionTask(src_path, target_ext, output_dir, options)
            self.tasks[task.id] = task
            return task

    def remove_task(self, task_id: str):
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == "running":
                    task.cancel()
                del self.tasks[task_id]

    def clear_completed(self):
        with self.lock:
            to_del = [tid for tid, t in self.tasks.items() if t.status in ("completed", "error", "cancelled")]
            for tid in to_del:
                del self.tasks[tid]

    def start_batch(self):
        """Avvia la conversione di tutti i task in coda in un thread worker dedicato."""
        if self.worker_thread and self.worker_thread.is_alive():
            return  # Già in esecuzione

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def start_single(self, task_id: str):
        """Avvia un singolo task se non è già in corso un batch."""
        def _run():
            with self.lock:
                task = self.tasks.get(task_id)
            if task and task.status in ("queued", "error"):
                self._execute_task(task)

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stop_all(self):
        """Richiede l'annullamento di tutti i task."""
        with self.lock:
            self.is_running = False
            for t in self.tasks.values():
                if t.status in ("queued", "running"):
                    t.cancel()

    def _process_queue(self):
        """Loop di elaborazione sequenziale della coda per mantenere basso il consumo di RAM."""
        while self.is_running:
            task_to_run = None
            with self.lock:
                for task in self.tasks.values():
                    if task.status == "queued" and not task.cancelled:
                        task_to_run = task
                        break

            if not task_to_run:
                break

            self._execute_task(task_to_run)

        self.is_running = False
        if self.on_all_completed:
            self.on_all_completed()

    def _execute_task(self, task: ConversionTask):
        task.status = "running"
        task.progress = 5
        task.status_message = "Avvio conversione..."
        self._notify_update(task)

        def progress_cb(pct: int, msg: str):
            task.progress = pct
            task.status_message = msg
            self._notify_update(task)

        start_time = time.time()

        try:
            # Determinazione del motore corretto in base a categoria e formati
            s_ext = task.src_ext
            d_ext = task.target_ext
            cat = task.category

            # 1. Documenti (PDF -> DOCX, DOCX -> PDF, PDF -> PNG/TXT, TXT -> PDF)
            if cat == CATEGORY_DOCUMENT or (s_ext in ("pdf", "docx") and d_ext in ("pdf", "docx", "txt", "md", "png", "jpg")):
                res = convert_document(task.src_path, task.dst_path, task.options, progress_cb)

            # 2. Immagini (Pillow / pillow-heif)
            elif cat == CATEGORY_IMAGE or (cat == CATEGORY_IMAGE and d_ext == "pdf"):
                res = convert_image(task.src_path, task.dst_path, task.options, progress_cb)

            # 3. Audio & Video (FFmpeg)
            elif cat in (CATEGORY_VIDEO, CATEGORY_AUDIO) or (cat == CATEGORY_VIDEO and d_ext in ("mp3", "wav", "flac", "aac", "gif")):
                res = convert_media(task.src_path, task.dst_path, task.options, progress_cb, task.is_cancelled)

            # 4. Dati e Tabelle (Pandas / OpenPyXL)
            elif cat == CATEGORY_DATA or (s_ext in ("csv", "xlsx", "json", "xml", "html") and d_ext in ("csv", "xlsx", "json", "xml", "html")):
                res = convert_data(task.src_path, task.dst_path, task.options, progress_cb)

            else:
                raise ValueError(f"Nessun motore di conversione compatibile per {s_ext} ➔ {d_ext}")

            if task.cancelled:
                task.status = "cancelled"
                task.status_message = "Conversione annullata"
            else:
                task.status = "completed"
                task.progress = 100
                elapsed = time.time() - start_time
                res["elapsed_sec"] = f"{elapsed:.2f}s"
                task.stats = res
                task.status_message = f"Completato in {elapsed:.1f}s"

                if self.on_task_complete:
                    self.on_task_complete(task)

        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.status_message = f"Errore: {str(e)[:45]}..."
            if self.on_task_error:
                self.on_task_error(task, str(e))

        finally:
            self._notify_update(task)

    def _notify_update(self, task: ConversionTask):
        if self.on_task_update:
            self.on_task_update(task)
