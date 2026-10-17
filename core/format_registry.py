"""
Registro dei formati, categorie e matrici di compatibilità per il Convertitore Universale.
Fornisce anche spiegazioni tecniche dettagliate su cosa accade 'sotto il cofano' per ciascuna conversione.
"""

from typing import Dict, List, Tuple, Optional

# Categorie principali
CATEGORY_IMAGE = "Immagini"
CATEGORY_VIDEO = "Video"
CATEGORY_AUDIO = "Audio"
CATEGORY_DATA = "Dati e Tabelle"
CATEGORY_DOCUMENT = "Documenti"

# Mappatura estensioni -> Categoria
EXTENSION_TO_CATEGORY: Dict[str, str] = {
    # Immagini
    "png": CATEGORY_IMAGE,
    "jpg": CATEGORY_IMAGE,
    "jpeg": CATEGORY_IMAGE,
    "webp": CATEGORY_IMAGE,
    "bmp": CATEGORY_IMAGE,
    "ico": CATEGORY_IMAGE,
    "tiff": CATEGORY_IMAGE,
    "tif": CATEGORY_IMAGE,
    "gif": CATEGORY_IMAGE,
    "heic": CATEGORY_IMAGE,
    "heif": CATEGORY_IMAGE,
    "ppm": CATEGORY_IMAGE,
    "pgm": CATEGORY_IMAGE,

    # Video
    "mp4": CATEGORY_VIDEO,
    "mkv": CATEGORY_VIDEO,
    "avi": CATEGORY_VIDEO,
    "mov": CATEGORY_VIDEO,
    "webm": CATEGORY_VIDEO,
    "flv": CATEGORY_VIDEO,
    "wmv": CATEGORY_VIDEO,
    "m4v": CATEGORY_VIDEO,
    "ts": CATEGORY_VIDEO,
    "mpg": CATEGORY_VIDEO,
    "mpeg": CATEGORY_VIDEO,

    # Audio
    "mp3": CATEGORY_AUDIO,
    "wav": CATEGORY_AUDIO,
    "flac": CATEGORY_AUDIO,
    "ogg": CATEGORY_AUDIO,
    "aac": CATEGORY_AUDIO,
    "m4a": CATEGORY_AUDIO,
    "wma": CATEGORY_AUDIO,
    "opus": CATEGORY_AUDIO,

    # Dati e Tabelle
    "csv": CATEGORY_DATA,
    "xlsx": CATEGORY_DATA,
    "xls": CATEGORY_DATA,
    "json": CATEGORY_DATA,
    "xml": CATEGORY_DATA,
    "html": CATEGORY_DATA,
    "tsv": CATEGORY_DATA,

    # Documenti
    "pdf": CATEGORY_DOCUMENT,
    "docx": CATEGORY_DOCUMENT,
    "txt": CATEGORY_DOCUMENT,
    "md": CATEGORY_DOCUMENT,
}

# Formati target disponibili per ciascuna estensione o categoria
IMAGE_TARGETS = ["png", "jpg", "webp", "bmp", "ico", "tiff", "gif", "pdf"]
VIDEO_TARGETS = ["mp4", "mkv", "avi", "mov", "webm", "gif", "mp3", "wav", "aac", "flac"]
AUDIO_TARGETS = ["mp3", "wav", "flac", "ogg", "aac", "m4a", "opus"]
DATA_TARGETS = ["csv", "xlsx", "json", "html", "xml"]
DOC_PDF_TARGETS = ["docx", "txt", "png", "jpg"]
DOC_DOCX_TARGETS = ["pdf", "txt", "html"]
DOC_TXT_TARGETS = ["pdf", "docx"]

# Icone / Badge per categoria
CATEGORY_ICONS = {
    CATEGORY_IMAGE: "🖼️",
    CATEGORY_VIDEO: "🎬",
    CATEGORY_AUDIO: "🎵",
    CATEGORY_DATA: "📊",
    CATEGORY_DOCUMENT: "📄",
}

def get_category(ext: str) -> str:
    """Restituisce la categoria di un'estensione (senza punto iniziale)."""
    return EXTENSION_TO_CATEGORY.get(ext.lower(), "Sconosciuto")

def get_compatible_targets(src_ext: str) -> List[str]:
    """Restituisce la lista dei formati di destinazione compatibili e significativi."""
    clean_ext = src_ext.lower().lstrip(".")
    cat = get_category(clean_ext)

    targets = []
    if cat == CATEGORY_IMAGE:
        targets = [t for t in IMAGE_TARGETS if t != clean_ext]
    elif cat == CATEGORY_VIDEO:
        targets = [t for t in VIDEO_TARGETS if t != clean_ext]
    elif cat == CATEGORY_AUDIO:
        targets = [t for t in AUDIO_TARGETS if t != clean_ext]
    elif cat == CATEGORY_DATA:
        targets = [t for t in DATA_TARGETS if t != clean_ext]
    elif cat == CATEGORY_DOCUMENT:
        if clean_ext == "pdf":
            targets = DOC_PDF_TARGETS
        elif clean_ext == "docx":
            targets = DOC_DOCX_TARGETS
        else:
            targets = DOC_TXT_TARGETS
    else:
        # Fallback generico
        targets = ["txt", "pdf"]

    return targets

def get_explanation(src_ext: str, dst_ext: str) -> Dict[str, str]:
    """
    Fornisce la spiegazione tecnica dettagliata su cosa accade realmente a livello binario
    durante la conversione specifica, dimostrando che non si tratta di una semplice rinomina.
    """
    s = src_ext.lower().lstrip(".")
    d = dst_ext.lower().lstrip(".")
    s_cat = get_category(s)
    d_cat = get_category(d)

    # 1. IMMAGINI
    if s_cat == CATEGORY_IMAGE and (d_cat == CATEGORY_IMAGE or d == "pdf"):
        engine = "Pillow (PIL) + pillow-heif"
        if s in ("heic", "heif"):
            desc = (
                "Decodifica il contenitore compresso HEIF di Apple/Samsung estraendo i piani "
                "di luminanza e crominanza YUV, converte lo spazio colore in matrice sRGB "
                f"e ricodifica i pixel secondo la specifica {d.upper()}."
            )
        elif d in ("jpg", "jpeg", "bmp") and s in ("png", "webp"):
            desc = (
                f"Decodifica i pixel grezzi con canale alfa di trasparenza (RGBA). "
                f"Poiché il formato {d.upper()} non supporta la trasparenza, il motore "
                "esegue un compositing Alpha-Blending su sfondo neutro, converte in RGB "
                "e applica la compressione con quantizzazione DCT."
            )
        elif d == "ico":
            desc = (
                "Decodifica l'immagine sorgente, genera frame multipli con ricampionamento "
                "LANCZOS di alta qualità (16x16, 32x32, 48x48, 64x64, 128x128, 256x256) "
                "e impacchetta la directory di icone nell'header binario standard di Windows ICO."
            )
        elif d == "pdf":
            desc = (
                "Estrae i dati raster dell'immagine e costruisce un flusso vettoriale PDF "
                "con coordinate di pagina corrette (72/300 DPI) incorporando l'immagine come XObject."
            )
        else:
            desc = (
                f"Decodifica la matrice bidimensionale dei pixel da {s.upper()} in memoria RAM, "
                f"ricostruisce i canali cromatici e comprime il flusso binario con i filtri nativi di {d.upper()}."
            )
        return {
            "title": f"Conversione Raster: {s.upper()} ➔ {d.upper()}",
            "engine": engine,
            "category": CATEGORY_IMAGE,
            "how_it_works": desc,
            "why_not_rename": (
                "Se rinominassi semplicemente il file, l'header binario e l'algoritmo di compressione "
                "non corrisponderebbero all'estensione e qualsiasi visualizzatore o app darebbe errore di file corrotto."
            )
        }

    # 2. AUDIO & VIDEO (FFmpeg)
    if s_cat in (CATEGORY_VIDEO, CATEGORY_AUDIO) or (s_cat == CATEGORY_VIDEO and d in ("mp3", "wav", "flac", "aac", "gif")):
        engine = "FFmpeg Core (Subprocess ad alte prestazioni)"
        if s_cat == CATEGORY_VIDEO and d in ("mp3", "wav", "aac", "flac", "ogg"):
            desc = (
                f"Demultiplexa il contenitore {s.upper()}, scarta lo stream video (-vn), "
                f"estrae i campioni audio PCM grezzi a virgola mobile, ed effettua la ricodifica "
                f"con il codec target ({'LAME' if d == 'mp3' else d.upper()}) al bitrate specificato."
            )
        elif s_cat == CATEGORY_VIDEO and d == "gif":
            desc = (
                "Esegue una conversione a due passaggi: analizza i fotogrammi con il filtro palettegen "
                "per calcolare una tavolozza ottimale a 256 colori, e poi applica paletteuse con dithering "
                "Lanczos per una GIF animata nitida e fluida."
            )
        else:
            desc = (
                f"Demultiplexa il contenitore {s.upper()}, decodifica i flussi elementari con i codec "
                f"sorgente (es. H.264, VP9, HEVC, AAC), ricalcola i timestamp (PTS/DTS) e ricodifica "
                f"nel contenitore {d.upper()} utilizzando i codec target raccomandati."
            )
        return {
            "title": f"Transcodifica Multimediale: {s.upper()} ➔ {d.upper()}",
            "engine": engine,
            "category": CATEGORY_VIDEO if s_cat == CATEGORY_VIDEO else CATEGORY_AUDIO,
            "how_it_works": desc,
            "why_not_rename": (
                "I contenitori multimediali usano strutture a pacchetti (Atom MOOV/MDAT per MP4, EBML per MKV/WEBM). "
                "Rinominare un file lascia inalterati i pacchetti interni e rende il file illeggibile dai lettori hardware."
            )
        }

    # 3. DATI E TABELLE (Pandas / Openpyxl)
    if s_cat == CATEGORY_DATA and d_cat == CATEGORY_DATA:
        engine = "Pandas DataFrame + OpenPyXL Engine"
        desc = (
            f"Esegue il parsing sintattico della struttura di {s.upper()}, valida i tipi di dato per colonna "
            f"(interi, decimali, date, stringhe) istanziando una tabella relazionale in memoria, e rigenera "
            f"la serializzazione formattata nel formato {d.upper()}."
        )
        return {
            "title": f"Serializzazione Dati: {s.upper()} ➔ {d.upper()}",
            "engine": engine,
            "category": CATEGORY_DATA,
            "how_it_works": desc,
            "why_not_rename": (
                "Un file CSV è testo puro con virgole, mentre un file XLSX è un archivio compresso ZIP contenente "
                "decine di file XML conforme allo standard OpenXML. Rinominare un CSV in .xlsx lo rende totalmente illeggibile da Excel."
            )
        }

    # 4. DOCUMENTI (pdf2docx, docx2pdf, PyMuPDF, reportlab)
    if s_cat == CATEGORY_DOCUMENT or s in ("pdf", "docx") or d in ("pdf", "docx"):
        engine = "pdf2docx / docx2pdf / PyMuPDF"
        if s == "pdf" and d == "docx":
            desc = (
                "Analizza il flusso vettoriale del PDF, estrae le coordinate dei glifi tipografici, "
                "identifica i confini delle tabelle e la gerarchia visiva dei titoli, "
                "e ricostruisce l'albero XML WordprocessingML nativo con stili e margini."
            )
        elif s == "docx" and d == "pdf":
            desc = (
                "Interroga il sottosistema di impaginazione e layout tipografico per rasterizzare "
                "i paragrafi, margini e interruzioni di pagina, generando un documento PDF vettoriale standard."
            )
        elif s == "pdf" and d in ("png", "jpg"):
            desc = (
                "Interpreta la pagina PDF come viewport vettoriale ed esegue il rastering "
                "ad alta risoluzione (300 DPI) per generare un'immagine nitida di ciascuna pagina."
            )
        else:
            desc = (
                f"Estrae i blocchi di testo, caratteri e formattazione da {s.upper()} "
                f"e ricompone il documento secondo gli standard di {d.upper()}."
            )
        return {
            "title": f"Ricostruzione Documentale: {s.upper()} ➔ {d.upper()}",
            "engine": engine,
            "category": CATEGORY_DOCUMENT,
            "how_it_works": desc,
            "why_not_rename": (
                "PDF e DOCX hanno strutture binarie completamente opposte: PDF è un formato di disegno a pagina statica, "
                "mentre DOCX è un flusso dinamico di testo XML a impaginazione fluida. Una semplice rinomina provocherebbe un crash."
            )
        }

    # Fallback
    return {
        "title": f"Conversione: {s.upper()} ➔ {d.upper()}",
        "engine": "Motore Universale",
        "category": "Generico",
        "how_it_works": "Decodifica il formato di origine e ricodifica nel formato di destinazione.",
        "why_not_rename": "I formati hanno specifiche binarie incompatibili tra loro."
    }
