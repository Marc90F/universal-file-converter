"""
Universal File Converter — Google Colab & Web Cloud Edition.
Interfaccia Web moderna (Gradio) per Google Colab e server cloud.
Permette conversioni reali di file (immagini, video, audio, dati e documenti)
con decodifica e ricodifica binaria, accessibile da qualsiasi browser (PC, smartphone Android, iPhone).
"""

import os
import sys
import shutil
import tempfile
import zipfile
import traceback
from typing import List, Optional, Tuple, Dict, Any

# Assicura che la root del progetto sia in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    import gradio as gr
except ImportError:
    raise ImportError("Gradio non è installato. Esegui: pip install gradio")

from core.format_registry import (
    get_category,
    get_compatible_targets,
    get_explanation,
    CATEGORY_ICONS,
    CATEGORY_IMAGE,
    CATEGORY_VIDEO,
    CATEGORY_AUDIO,
    CATEGORY_DATA,
    CATEGORY_DOCUMENT,
    IMAGE_TARGETS,
    VIDEO_TARGETS,
    AUDIO_TARGETS,
    DATA_TARGETS,
)
from core.ffmpeg_manager import find_ffmpeg
from engines.image_engine import convert_image
from engines.media_engine import convert_media
from engines.data_engine import convert_data
from engines.doc_engine import convert_document

# Lista di tutti i target possibili per la modalità batch
ALL_KNOWN_TARGETS = sorted(list(set(
    IMAGE_TARGETS + VIDEO_TARGETS + AUDIO_TARGETS + DATA_TARGETS + ["pdf", "docx", "txt", "md"]
)))


def _format_explanation(src_ext: str, dst_ext: str) -> str:
    """Formatta la spiegazione tecnica del perché non è un finto cambio di estensione."""
    if not src_ext or not dst_ext:
        return "Seleziona un file e un formato di destinazione per visualizzare i dettagli tecnici."

    expl = get_explanation(src_ext, dst_ext)
    cat = expl.get("category", get_category(src_ext))
    icon = CATEGORY_ICONS.get(cat, "📁")

    return f"""### {icon} Spiegazione Tecnica ({src_ext.upper()} ➔ {dst_ext.upper()})
- **Categoria di Conversione:** `{cat}`
- **Motore Utilizzato:** `{expl.get('engine', 'Motore Standard')}`

#### ⚙️ Come funziona la decodifica/ricodifica reale:
{expl.get('how_it_works', 'I flussi vengono decodificati in memoria e ricodificati da zero nel formato target.')}

#### 🛡️ Perché non è un semplice cambio di estensione:
{expl.get('why_not_rename', 'Rinominare il file corromperebbe la struttura binaria; questa conversione ricostruisce l\'intero file nel rispetto degli standard.')}
"""


def on_file_uploaded(file_path: Optional[str]):
    """Aggiorna dinamicamente i formati disponibili e le informazioni quando l'utente carica un file."""
    if not file_path:
        return (
            gr.update(choices=[], value=None),
            "Nessun file selezionato. Carica o trascina un file sopra.",
            ""
        )

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    category = get_category(ext)
    icon = CATEGORY_ICONS.get(category, "📁")

    targets = get_compatible_targets(ext)
    if not targets:
        targets = ["pdf", "txt", "zip"]

    default_target = targets[0] if targets else "pdf"

    info_md = f"""### {icon} File Rilevato: **`{filename}`**
- **Estensione:** `.{ext.upper()}`
- **Categoria:** **{category}**
- **Formati di destinazione consigliati:** {len(targets)} formati compatibili.
"""

    explanation = _format_explanation(ext, default_target)
    return (
        gr.update(choices=[t.upper() for t in targets], value=default_target.upper()),
        info_md,
        explanation
    )


def on_target_changed(file_path: Optional[str], target_format: Optional[str]):
    """Aggiorna il box informativo quando l'utente seleziona un formato diverso dal dropdown."""
    if not file_path or not target_format:
        return ""
    src_ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    dst_ext = target_format.lower().lstrip(".")
    return _format_explanation(src_ext, dst_ext)


def convert_single_file(
    file_path: Optional[str],
    target_format: Optional[str],
    img_quality: int,
    audio_bitrate: str,
    video_quality: str,
    progress=gr.Progress()
) -> Tuple[Optional[str], str]:
    """Esegue la conversione reale del singolo file richiamando il motore appropriato."""
    if not file_path:
        return None, "⚠️ Errore: Nessun file sorgente caricato."
    if not target_format:
        return None, "⚠️ Errore: Nessun formato di destinazione selezionato."

    src_name = os.path.basename(file_path)
    base_name = os.path.splitext(src_name)[0]
    src_ext = os.path.splitext(src_name)[1].lower().lstrip(".")
    dst_ext = target_format.lower().lstrip(".")
    category = get_category(src_ext)

    out_dir = tempfile.mkdtemp(prefix="ufc_single_")
    dst_path = os.path.join(out_dir, f"{base_name}.{dst_ext}")

    options: Dict[str, Any] = {
        "quality": int(img_quality),
        "audio_bitrate": str(audio_bitrate),
        "video_quality": str(video_quality),
    }

    def _prog_cb(pct: int, msg: str):
        progress(pct / 100.0, desc=msg)

    try:
        progress(0.1, desc=f"Avvio conversione reale di {src_name}...")

        if category == CATEGORY_IMAGE:
            convert_image(file_path, dst_path, options=options, progress_callback=_prog_cb)
        elif category in (CATEGORY_VIDEO, CATEGORY_AUDIO):
            convert_media(file_path, dst_path, options=options, progress_callback=_prog_cb)
        elif category == CATEGORY_DATA:
            convert_data(file_path, dst_path, options=options, progress_callback=_prog_cb)
        elif category == CATEGORY_DOCUMENT:
            convert_document(file_path, dst_path, options=options, progress_callback=_prog_cb)
        else:
            # Tenta fallback con i vari motori
            try:
                convert_image(file_path, dst_path, options=options, progress_callback=_prog_cb)
            except Exception:
                convert_data(file_path, dst_path, options=options, progress_callback=_prog_cb)

        # Gestione speciale caso PDF -> più immagini
        all_created = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]
        
        if len(all_created) > 1:
            zip_dst = os.path.join(out_dir, f"{base_name}_pagine_{dst_ext}.zip")
            with zipfile.ZipFile(zip_dst, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in all_created:
                    zf.write(f, os.path.basename(f))
            return zip_dst, f"✅ Conversione completata con successo! Generate {len(all_created)} pagine, raggruppate in ZIP."

        if os.path.exists(dst_path):
            size_kb = os.path.getsize(dst_path) / 1024
            return dst_path, f"✅ Conversione completata con successo: **{os.path.basename(dst_path)}** ({size_kb:.1f} KB)"
        elif all_created:
            return all_created[0], f"✅ File convertito con successo: **{os.path.basename(all_created[0])}**"
        else:
            return None, "⚠️ Il motore non ha generato alcun file di output."

    except Exception as e:
        err_msg = f"❌ Errore durante la conversione: {str(e)}\n\n{traceback.format_exc()}"
        return None, err_msg


def convert_batch_files(
    file_paths: Optional[List[str]],
    target_format: Optional[str],
    img_quality: int,
    audio_bitrate: str,
    video_quality: str,
    progress=gr.Progress()
) -> Tuple[Optional[str], str]:
    """Esegue la conversione batch di multipli file e produce un file .zip con tutti i risultati."""
    if not file_paths:
        return None, "⚠️ Nessun file selezionato per la conversione batch."
    if not target_format:
        return None, "⚠️ Nessun formato di destinazione selezionato."

    out_dir = tempfile.mkdtemp(prefix="ufc_batch_")
    total_files = len(file_paths)
    success_count = 0
    failed_count = 0
    converted_files = []

    dst_ext = target_format.lower().lstrip(".")
    options = {
        "quality": int(img_quality),
        "audio_bitrate": str(audio_bitrate),
        "video_quality": str(video_quality),
    }

    for idx, fpath in enumerate(file_paths):
        fname = os.path.basename(fpath)
        base = os.path.splitext(fname)[0]
        src_ext = os.path.splitext(fname)[1].lower().lstrip(".")
        cat = get_category(src_ext)

        progress(idx / total_files, desc=f"Convertendo ({idx+1}/{total_files}): {fname}...")
        cur_dst = os.path.join(out_dir, f"{base}.{dst_ext}")

        try:
            if cat == CATEGORY_IMAGE:
                convert_image(fpath, cur_dst, options=options)
            elif cat in (CATEGORY_VIDEO, CATEGORY_AUDIO):
                convert_media(fpath, cur_dst, options=options)
            elif cat == CATEGORY_DATA:
                convert_data(fpath, cur_dst, options=options)
            elif cat == CATEGORY_DOCUMENT:
                convert_document(fpath, cur_dst, options=options)
            else:
                convert_image(fpath, cur_dst, options=options)

            if os.path.exists(cur_dst):
                converted_files.append(cur_dst)
                success_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    progress(1.0, desc="Compressione risultati in archivio ZIP...")
    if not converted_files:
        return None, f"❌ Nessun file è stato convertito con successo ({failed_count} falliti)."

    zip_path = os.path.join(out_dir, f"Universal_File_Converter_Batch_{dst_ext.upper()}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for cf in converted_files:
            zf.write(cf, os.path.basename(cf))

    status_msg = f"🎉 Conversione batch completata! **{success_count} file convertiti** con successo ({failed_count} errori). Scarica lo ZIP qui sotto."
    return zip_path, status_msg


def get_system_diagnostic_markdown() -> str:
    """Restituisce lo stato dei motori e dell'ambiente in Markdown."""
    ffmpeg_bin = find_ffmpeg()
    ffmpeg_status = f"✅ Disponibile (`{ffmpeg_bin}`)" if ffmpeg_bin else "⚠️ Non rilevato nel PATH (alcuni formati video/audio potrebbero richiedere l'installazione)"

    # Verifica LibreOffice
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    lo_status = f"✅ Disponibile (`{soffice}`)" if soffice else "ℹ️ Non presente (utilizzato fallback nativo ReportLab)"

    # Verifica librerie Python
    def _chk(mod_name: str) -> str:
        try:
            __import__(mod_name)
            return "✅ Installato"
        except ImportError:
            return "❌ Non installato"

    has_pdf_raster = "✅ Installato" if _chk('pymupdf') == "✅ Installato" or _chk('fitz') == "✅ Installato" else "❌ Non installato"

    return f"""### 🩺 Stato dei Motori di Conversione Cloud

| Componente / Motore | Ruolo | Stato Ambiente |
|---|---|---|
| **Pillow + pillow-heif** | Rastering pixel, canali colore, WebP, HEIC/HEIF Apple | {_chk('PIL')} ({_chk('pillow_heif')}) |
| **FFmpeg Subprocess** | Decodifica/ricodifica H.264, AAC, MP3, Vorbis, WebM, GIF animata | {ffmpeg_status} |
| **Pandas + OpenPyXL** | Parsing tabellare, fogli XLSX formattati, CSV, JSON, XML | {_chk('pandas')} ({_chk('openpyxl')}) |
| **PyMuPDF & pdf2docx** | Rendering vettoriale PDF a 300 DPI, estrazione layout Word | {has_pdf_raster} ({_chk('pdf2docx')}) |
| **ReportLab & python-docx** | Generazione tipografica documenti PDF da zero | {_chk('reportlab')} ({_chk('docx')}) |
| **LibreOffice Headless** | Conversione fedele DOCX/PPTX/ODT ➔ PDF su server Linux | {lo_status} |

🛡️ **Privacy & Sicurezza:** Tutti i file caricati vengono elaborati localmente nell'istanza temporanea di Google Colab e cancellati automaticamente al termine della sessione.
"""


def build_colab_interface() -> Tuple[gr.Blocks, Any]:
    """Costruisce l'interfaccia Gradio completa con tema dark coordinato."""
    custom_theme = gr.themes.Soft(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="slate"
    ).set(
        body_background_fill="#0f0f17",
        body_background_fill_dark="#0f0f17",
        block_background_fill="#181825",
        block_background_fill_dark="#181825",
        block_border_width="1px",
        block_border_color="#2b2b3d",
        button_primary_background_fill="#e53935",
        button_primary_background_fill_hover="#c62828",
        button_primary_text_color="#ffffff",
    )

    with gr.Blocks(title="Universal File Converter — Cloud & Mobile") as demo:
        gr.Markdown(
            """
            # 🚀 Universal File Converter
            ### Edizione Web Cloud & Mobile • Decodifica & Ricodifica Reale
            Elabora immagini, video, audio, fogli di calcolo e documenti PDF/Word sfruttando la potenza cloud di Google Colab.
            Accessibile comodamente da qualsiasi browser su **PC, smartphone Android, iPhone e tablet**.
            """
        )

        with gr.Tabs():
            # TAB 1: CONVERSIONE SINGOLA
            with gr.TabItem("📁 Conversione Singola & Avanzata"):
                with gr.Row():
                    with gr.Column(scale=1):
                        single_in = gr.File(
                            label="Trascina o tocca per selezionare il file da convertire",
                            file_count="single",
                            type="filepath"
                        )
                        file_info = gr.Markdown("Carica un file per visualizzarne le informazioni e i formati compatibili.")

                        target_dropdown = gr.Dropdown(
                            label="Scegli il Formato di Destinazione",
                            choices=[],
                            interactive=True
                        )

                        with gr.Accordion("⚙️ Opzioni Avanzate di Conversione", open=False):
                            img_qual = gr.Slider(
                                minimum=10,
                                maximum=100,
                                value=95,
                                step=1,
                                label="Qualità Immagine (Pillow / WebP / JPG)"
                            )
                            aud_bit = gr.Radio(
                                choices=["128k", "192k", "256k", "320k"],
                                value="192k",
                                label="Bitrate Audio (FFmpeg)"
                            )
                            vid_qual = gr.Radio(
                                choices=["high", "medium", "low"],
                                value="medium",
                                label="Profilo Qualità Video (CRF FFmpeg)"
                            )

                        convert_single_btn = gr.Button("🚀 AVVIA CONVERSIONE REALE", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        single_status = gr.Markdown("In attesa che venga avviata la conversione...")
                        single_out = gr.File(label="📥 Scarica File Convertito")
                        single_expl = gr.Markdown("")

                # Collegamento eventi
                single_in.change(
                    fn=on_file_uploaded,
                    inputs=[single_in],
                    outputs=[target_dropdown, file_info, single_expl]
                )
                target_dropdown.change(
                    fn=on_target_changed,
                    inputs=[single_in, target_dropdown],
                    outputs=[single_expl]
                )
                convert_single_btn.click(
                    fn=convert_single_file,
                    inputs=[single_in, target_dropdown, img_qual, aud_bit, vid_qual],
                    outputs=[single_out, single_status]
                )

            # TAB 2: CONVERSIONE BATCH (MULTIFILE)
            with gr.TabItem("⚡ Conversione Batch (Multipli File)"):
                gr.Markdown("Carica più file contemporaneamente e seleziona il formato desiderato. Riceverai un archivio ZIP con tutti i file convertiti.")
                with gr.Row():
                    with gr.Column(scale=1):
                        batch_in = gr.File(
                            label="Trascina o seleziona più file",
                            file_count="multiple",
                            type="filepath"
                        )
                        batch_target = gr.Dropdown(
                            label="Formato di destinazione per tutti i file",
                            choices=[t.upper() for t in ALL_KNOWN_TARGETS],
                            value="PDF"
                        )
                        batch_btn = gr.Button("⚡ CONVERTI TUTTI I FILE (BATCH)", variant="primary", size="lg")

                    with gr.Column(scale=1):
                        batch_status = gr.Markdown("Seleziona i file e premi il pulsante per avviare il processo batch.")
                        batch_out = gr.File(label="📥 Scarica Archivio ZIP Convertito")

                batch_btn.click(
                    fn=convert_batch_files,
                    inputs=[batch_in, batch_target, img_qual, aud_bit, vid_qual],
                    outputs=[batch_out, batch_status]
                )

            # TAB 3: STATO MOTORI & DIAGNOSTICA
            with gr.TabItem("🩺 Diagnostica Motori"):
                diag_md = gr.Markdown(get_system_diagnostic_markdown())
                refresh_btn = gr.Button("🔄 Aggiorna Stato Motori")
                refresh_btn.click(fn=get_system_diagnostic_markdown, outputs=[diag_md])

        gr.Markdown(
            """
            ---
            <div style="text-align: center; color: #a6adc8; font-size: 0.85rem;">
                Universal File Converter Portable & Cloud • 100% Open Source • Nessun dato salvato su server esterni
            </div>
            """
        )

    return demo, custom_theme


def launch_colab(share: bool = True, server_port: int = 7860, debug: bool = False):
    """Avvia l'app Gradio generando il link pubblico con share=True per smartphone e PC."""
    demo, custom_theme = build_colab_interface()
    demo.queue()
    try:
        demo.launch(
            share=share,
            server_port=server_port,
            theme=custom_theme,
            debug=debug,
            show_error=True
        )
    except TypeError:
        demo.launch(
            share=share,
            server_port=server_port,
            debug=debug,
            show_error=True
        )


if __name__ == "__main__":
    share_flag = "--share" in sys.argv or "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ
    print(f"[*] Avvio Universal File Converter Cloud (share={share_flag})...")
    launch_colab(share=share_flag)
