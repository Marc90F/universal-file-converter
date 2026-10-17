"""
Verificatore e gestore automatico delle dipendenze per l'ambiente portatile.
Permette l'avvio su qualsiasi PC con Python standard e l'installazione automatica
con 1 click dei motori di conversione mancanti.
"""

import sys
import subprocess
import importlib.util
from typing import Dict, List, Tuple, Callable, Optional
from core.ffmpeg_manager import is_ffmpeg_available, get_startupinfo

# Definizione dei componenti e dei rispettivi moduli e pacchetti pip
COMPONENTS = [
    {
        "id": "pillow",
        "name": "Pillow (PIL)",
        "module": "PIL",
        "pip": "pillow",
        "category": "Immagini",
        "desc": "Motore raster per decodifica/ricodifica di pixel grezzi (PNG, JPG, WEBP, BMP, ICO, TIFF, GIF)."
    },
    {
        "id": "pillow_heif",
        "name": "Pillow-HEIF",
        "module": "pillow_heif",
        "pip": "pillow-heif",
        "category": "Immagini",
        "desc": "Supporto per foto ad alta efficienza Apple iPhone / Samsung HEIC/HEIF."
    },
    {
        "id": "ffmpeg",
        "name": "FFmpeg Core",
        "module": None,  # Binario esterno gestito da ffmpeg_manager
        "pip": None,
        "category": "Audio e Video",
        "desc": "Demuxer e codec universale per stream audio e video (MP4, MKV, AVI, MP3, WAV, FLAC)."
    },
    {
        "id": "pandas",
        "name": "Pandas",
        "module": "pandas",
        "pip": "pandas",
        "category": "Dati e Tabelle",
        "desc": "Motore di analisi e serializzazione strutturata DataFrame per CSV, JSON, HTML, XML."
    },
    {
        "id": "openpyxl",
        "name": "OpenPyXL",
        "module": "openpyxl",
        "pip": "openpyxl",
        "category": "Dati e Tabelle",
        "desc": "Generatore nativo di fogli di calcolo Excel XLSX OpenXML."
    },
    {
        "id": "pdf2docx",
        "name": "pdf2docx",
        "module": "pdf2docx",
        "pip": "pdf2docx",
        "category": "Documenti",
        "desc": "Ricostruttore di layout, paragrafi e tabelle da PDF a documento Word DOCX."
    },
    {
        "id": "docx2pdf",
        "name": "docx2pdf",
        "module": "docx2pdf",
        "pip": "docx2pdf",
        "category": "Documenti",
        "desc": "Convertitore ad alta fedeltà da DOCX a PDF (supporta Microsoft Word COM su Windows)."
    },
    {
        "id": "pymupdf",
        "name": "PyMuPDF",
        "module": "pymupdf",
        "pip": "pymupdf",
        "category": "Documenti",
        "desc": "Rendering di pagine PDF in immagini ad alta risoluzione ed estrazione di testi vettoriali."
    },
    {
        "id": "customtkinter",
        "name": "CustomTkinter",
        "module": "customtkinter",
        "pip": "customtkinter",
        "category": "Interfaccia",
        "desc": "UI moderna e reattiva con supporto Dark/Light Mode stile Convertio."
    }
]

def check_module_installed(module_name: str) -> bool:
    """Verifica se un modulo Python è importabile senza lanciarlo per intero."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False

def check_all_components() -> List[Dict]:
    """Ispeziona lo stato di tutti i componenti necessari."""
    status_list = []
    for comp in COMPONENTS:
        if comp["id"] == "ffmpeg":
            installed = is_ffmpeg_available()
        else:
            installed = check_module_installed(comp["module"])

        status_list.append({
            **comp,
            "installed": installed
        })
    return status_list

def are_core_engines_ready() -> bool:
    """Verifica se almeno i motori base per iniziare sono pronti."""
    comps = check_all_components()
    # Verifica pillow e customtkinter
    essential = [c["installed"] for c in comps if c["id"] in ("pillow", "customtkinter")]
    return all(essential)

def install_pip_packages(packages: List[str], output_callback: Optional[Callable[[str], None]] = None) -> bool:
    """
    Installa i pacchetti pip mancanti usando l'interprete Python corrente.
    Esegue lo streaming dell'output per informare l'utente.
    """
    if not packages:
        return True

    cmd = [sys.executable, "-m", "pip", "install", *packages]
    if output_callback:
        output_callback(f"Esecuzione: {' '.join(cmd)}\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=get_startupinfo()
        )

        for line in process.stdout:
            if output_callback:
                output_callback(line.rstrip())

        process.wait()
        return process.returncode == 0
    except Exception as e:
        if output_callback:
            output_callback(f"Errore durante l'installazione: {e}\n")
        return False
