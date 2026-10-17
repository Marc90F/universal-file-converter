"""
Motore di conversione immagini basato su Pillow e pillow-heif.
Decodifica la matrice di pixel grezzi, converte gli spazi colore (es. da RGBA a RGB per rimozione alfa),
gestisce la generazione multi-risoluzione per ICO, e ricodifica nel formato di destinazione.
"""

import os
from typing import Dict, Any, Callable, Optional
from PIL import Image, ImageOps

# Registrazione supporto HEIF/HEIC se disponibile
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

def convert_image(
    src_path: str,
    dst_path: str,
    options: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Dict[str, Any]:
    """
    Esegue la conversione reale del file immagine decodificando e ricodificando i pixel.
    """
    options = options or {}
    quality = int(options.get("quality", 95))
    resize = options.get("resize", None)  # es. (width, height) o None
    bg_color = options.get("bg_color", (255, 255, 255)) # Per rimozione canale alfa

    if progress_callback:
        progress_callback(10, f"Apertura e decodifica raster di {os.path.basename(src_path)}...")

    dst_ext = os.path.splitext(dst_path)[1].lower().lstrip(".")
    if dst_ext == "jpg":
        dst_ext = "jpeg"

    # Apertura immagine con Pillow e protezione Decompression Bomb
    try:
        with Image.open(src_path) as img:
            orig_format = img.format or "Sconosciuto"
            orig_mode = img.mode
            orig_size = img.size

            if progress_callback:
                progress_callback(30, f"Rilevato: {orig_size[0]}x{orig_size[1]}px ({orig_mode}). Elaborazione...")
    except Image.DecompressionBombError:
        raise RuntimeError("L'immagine supera le dimensioni di sicurezza (potenziale Decompression Bomb DoS). Rifiutata.")

    with Image.open(src_path) as img:

        # Gestione orientamento EXIF (es. foto scattate con smartphone)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Ridimensionamento opzionale se richiesto
        if resize and isinstance(resize, (tuple, list)) and len(resize) == 2:
            w, h = int(resize[0]), int(resize[1])
            if w > 0 and h > 0:
                img = img.resize((w, h), Image.Resampling.LANCZOS)

        # Gestione canali e spazi colore
        # Formati che NON supportano il canale alfa (trasparenza)
        no_alpha_formats = ("jpeg", "bmp", "pdf")
        if dst_ext in no_alpha_formats:
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                if progress_callback:
                    progress_callback(50, "Compositing canale alfa su sfondo neutro (conversione RGBA ➔ RGB)...")
                # Crea sfondo bianco
                bg = Image.new("RGB", img.size, bg_color)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[3]) # Maschera canale alfa
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")
        elif dst_ext == "png":
            # PNG supporta sia RGBA che RGB
            if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                img = img.convert("RGBA")
        elif dst_ext == "webp":
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
        elif dst_ext == "ico":
            if img.mode != "RGBA":
                img = img.convert("RGBA")

        if progress_callback:
            progress_callback(75, f"Ricodifica e serializzazione in {dst_ext.upper()}...")

        save_kwargs = {}

        # Parametri di compressione e codifica per formato
        if dst_ext in ("jpeg", "jpg"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
            save_kwargs["progressive"] = True
        elif dst_ext == "webp":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6
        elif dst_ext == "png":
            save_kwargs["optimize"] = True
            save_kwargs["compress_level"] = 9
        elif dst_ext == "ico":
            # Genera icone multi-dimensione per Windows
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            # Filtra dimensioni maggiori di quella originale per evitare upscaling sfocato
            valid_sizes = [s for s in icon_sizes if s[0] <= max(orig_size) or s[0] == 32]
            if not valid_sizes:
                valid_sizes = [(32, 32)]
            save_kwargs["sizes"] = valid_sizes
        elif dst_ext in ("tiff", "tif"):
            save_kwargs["compression"] = "tiff_deflate"
        elif dst_ext == "pdf":
            save_kwargs["resolution"] = 100.0

        # Scrittura del nuovo file binario
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        img.save(dst_path, format=dst_ext.upper() if dst_ext != "ico" else "ICO", **save_kwargs)

    if progress_callback:
        progress_callback(100, f"Conversione completata: {os.path.basename(dst_path)}")

    orig_bytes = os.path.getsize(src_path)
    new_bytes = os.path.getsize(dst_path)

    return {
        "status": "success",
        "src": src_path,
        "dst": dst_path,
        "orig_size": orig_size,
        "orig_bytes": orig_bytes,
        "new_bytes": new_bytes,
        "compression_ratio": f"{((orig_bytes - new_bytes) / orig_bytes * 100):.1f}%" if orig_bytes > 0 else "0%"
    }
