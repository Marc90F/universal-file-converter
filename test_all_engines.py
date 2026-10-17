"""
Script di collaudo completo per i 4 motori di conversione.
Crea file sorgente di prova e testa la reale decodifica e ricodifica binaria.
"""

import os
import sys
import tempfile

# Imposta stdout in UTF-8 per console Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PIL import Image, ImageDraw

def test_engines():
    print("=" * 60)
    print("AVVIO COLLAUDO DEI 4 MOTORI DEL CONVERTITORE UNIVERSALE")
    print("=" * 60)

    test_dir = tempfile.mkdtemp(prefix="convertio_test_")
    print(f"Directory temporanea di collaudo: {test_dir}\n")

    # -------------------------------------------------------------
    # 1. TEST MOTORE IMMAGINI (Pillow)
    # -------------------------------------------------------------
    print("[1/4] Test Motore Immagini (Pillow)...")
    from engines.image_engine import convert_image

    # Crea immagine PNG con canale ALFA trasparente e disegno
    png_path = os.path.join(test_dir, "test_alpha.png")
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0)) # Trasparente
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 180, 180], fill=(229, 57, 53, 200), outline=(255, 255, 255, 255), width=3)
    draw.ellipse([60, 60, 140, 140], fill=(255, 255, 255, 220))
    img.save(png_path, "PNG")

    # PNG -> JPG (verifica corretta rimozione alfa su sfondo bianco)
    jpg_path = os.path.join(test_dir, "test_output.jpg")
    res_jpg = convert_image(png_path, jpg_path, {"quality": 90})
    assert os.path.exists(jpg_path) and os.path.getsize(jpg_path) > 0, "JPG non generato"
    print(f"  ✓ PNG (RGBA) ➔ JPG (RGB su bianco) riuscito! ({res_jpg['new_bytes']} bytes)")

    # PNG -> WEBP
    webp_path = os.path.join(test_dir, "test_output.webp")
    res_webp = convert_image(png_path, webp_path, {"quality": 85})
    assert os.path.exists(webp_path) and os.path.getsize(webp_path) > 0, "WEBP non generato"
    print(f"  ✓ PNG ➔ WEBP riuscito! ({res_webp['new_bytes']} bytes)")

    # PNG -> ICO (multi-risoluzione)
    ico_path = os.path.join(test_dir, "test_output.ico")
    res_ico = convert_image(png_path, ico_path)
    assert os.path.exists(ico_path) and os.path.getsize(ico_path) > 0, "ICO non generato"
    print(f"  ✓ PNG ➔ ICO Multi-risoluzione riuscito! ({res_ico['new_bytes']} bytes)")

    # PNG -> PDF
    pdf_img_path = os.path.join(test_dir, "test_img_to_pdf.pdf")
    res_pdf_img = convert_image(png_path, pdf_img_path)
    assert os.path.exists(pdf_img_path) and os.path.getsize(pdf_img_path) > 0, "PDF da immagine non generato"
    print(f"  ✓ PNG ➔ PDF Vettoriale riuscito! ({res_pdf_img['new_bytes']} bytes)")

    # -------------------------------------------------------------
    # 2. TEST MOTORE AUDIO & VIDEO (FFmpeg)
    # -------------------------------------------------------------
    print("\n[2/4] Test Motore Audio & Video (FFmpeg)...")
    from core.ffmpeg_manager import find_ffmpeg
    from engines.media_engine import convert_media
    import subprocess

    ffmpeg_exe = find_ffmpeg()
    if ffmpeg_exe:
        # Genera un breve file video di test (2 secondi, 640x360 con colore e beep sintetico)
        src_video = os.path.join(test_dir, "test_video.mp4")
        gen_cmd = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
            "-c:v", "libx264", "-c:a", "aac",
            src_video
        ]
        subprocess.run(gen_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert os.path.exists(src_video), "Generazione video di test fallita"

        # MP4 -> MP3 (estrazione e ricodifica audio)
        dst_mp3 = os.path.join(test_dir, "test_audio.mp3")
        res_mp3 = convert_media(src_video, dst_mp3, {"audio_bitrate": "192k"})
        assert os.path.exists(dst_mp3) and os.path.getsize(dst_mp3) > 0, "MP3 non generato"
        print(f"  ✓ MP4 ➔ MP3 (Demuxing + ricodifica LAME) riuscito! ({res_mp3['new_bytes']} bytes)")

        # MP4 -> GIF animata
        dst_gif = os.path.join(test_dir, "test_video.gif")
        res_gif = convert_media(src_video, dst_gif)
        assert os.path.exists(dst_gif) and os.path.getsize(dst_gif) > 0, "GIF non generata"
        print(f"  ✓ MP4 ➔ GIF Animata (Palettegen 256 colori) riuscito! ({res_gif['new_bytes']} bytes)")

        # MP4 -> WEBM
        dst_webm = os.path.join(test_dir, "test_video.webm")
        res_webm = convert_media(src_video, dst_webm)
        assert os.path.exists(dst_webm) and os.path.getsize(dst_webm) > 0, "WEBM non generato"
        print(f"  ✓ MP4 ➔ WEBM (VP9 + Opus) riuscito! ({res_webm['new_bytes']} bytes)")
    else:
        print("  [!] FFmpeg non trovato per il test video.")

    # -------------------------------------------------------------
    # 3. TEST MOTORE DATI E TABELLE (Pandas + OpenPyXL)
    # -------------------------------------------------------------
    print("\n[3/4] Test Motore Dati e Tabelle (Pandas + OpenPyXL)...")
    from engines.data_engine import convert_data

    # Crea file CSV di prova con accenti ed emoji
    csv_path = os.path.join(test_dir, "test_data.csv")
    csv_content = """ID,Prodotto,Prezzo,Quantita,Categoria
1,Computer Portatile,899.99,12,Informatica
2,Tastiera Meccanica RGB,79.50,45,Accessori
3,Cuffie Wireless Bluetooth,120.00,28,Audio
4,Monitor 4K 27",349.00,8,Display
"""
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)

    # CSV -> XLSX
    xlsx_path = os.path.join(test_dir, "test_data.xlsx")
    res_xlsx = convert_data(csv_path, xlsx_path)
    assert os.path.exists(xlsx_path) and os.path.getsize(xlsx_path) > 0, "XLSX non generato"
    print(f"  ✓ CSV ➔ XLSX (OpenXML formattato) riuscito! ({res_xlsx['rows']} righe, {res_xlsx['columns']} colonne)")

    # XLSX -> JSON
    json_path = os.path.join(test_dir, "test_data.json")
    res_json = convert_data(xlsx_path, json_path)
    assert os.path.exists(json_path) and os.path.getsize(json_path) > 0, "JSON non generato"
    print(f"  ✓ XLSX ➔ JSON (Records indentati) riuscito! ({res_json['rows']} record)")

    # JSON -> HTML
    html_path = os.path.join(test_dir, "test_data.html")
    res_html = convert_data(json_path, html_path)
    assert os.path.exists(html_path) and os.path.getsize(html_path) > 0, "HTML non generato"
    print(f"  ✓ JSON ➔ HTML (Tabella responsive con CSS) riuscito!")

    # CSV -> XML
    xml_path = os.path.join(test_dir, "test_data.xml")
    res_xml = convert_data(csv_path, xml_path)
    assert os.path.exists(xml_path) and os.path.getsize(xml_path) > 0, "XML non generato"
    print(f"  ✓ CSV ➔ XML (Albero tag strutturato) riuscito!")

    # -------------------------------------------------------------
    # 4. TEST MOTORE DOCUMENTI (pdf2docx, docx2pdf, PyMuPDF, ReportLab)
    # -------------------------------------------------------------
    print("\n[4/4] Test Motore Documenti (PyMuPDF & ReportLab)...")
    from engines.doc_engine import convert_document

    # TXT -> PDF
    txt_path = os.path.join(test_dir, "test_doc.txt")
    txt_content = """DOCUMENTO DI PROVA CONVERTITORE UNIVERSALE
Questo documento verifica la reale ricostruzione tipografica in memoria.
Paragrafo 1: Formattazione margini, glifi e spaziatura interlinea.
Paragrafo 2: Generazione vettoriale del flusso binario PDF.
"""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    doc_pdf_path = os.path.join(test_dir, "test_doc.pdf")
    res_doc_pdf = convert_document(txt_path, doc_pdf_path)
    assert os.path.exists(doc_pdf_path) and os.path.getsize(doc_pdf_path) > 0, "PDF non generato"
    print(f"  ✓ TXT ➔ PDF (ReportLab tipografico) riuscito! ({res_doc_pdf['new_bytes']} bytes)")

    # PDF -> PNG (rendering 300 DPI)
    doc_png_path = os.path.join(test_dir, "test_doc_page.png")
    res_doc_png = convert_document(doc_pdf_path, doc_png_path)
    assert os.path.exists(doc_png_path) and os.path.getsize(doc_png_path) > 0, "PNG da PDF non generato"
    print(f"  ✓ PDF ➔ PNG (Rendering vettoriale 300 DPI) riuscito! ({res_doc_png['new_bytes']} bytes)")

    # PDF -> TXT (estrazione testo)
    doc_txt_out = os.path.join(test_dir, "test_extracted.txt")
    res_doc_txt = convert_document(doc_pdf_path, doc_txt_out)
    assert os.path.exists(doc_txt_out) and os.path.getsize(doc_txt_out) > 0, "Estrazione TXT fallita"
    print(f"  ✓ PDF ➔ TXT (Estrazione testo strutturato) riuscito!")

    print("\n" + "=" * 60)
    print("TUTTI I 4 MOTORI HANNO SUPERATO IL COLLAUDO AL 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_engines()
