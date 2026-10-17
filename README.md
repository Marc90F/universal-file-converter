# 🔄 Universal File Converter — Convertitore Universale Reale
### Per Windows, macOS (Apple Silicon & Intel) e Linux

Un vero convertitore desktop universale ispirato a Convertio, scritto in Python.
A differenza di script che si limitano a rinominare l'estensione del file, questo software **decodifica realmente i flussi binari non compressi in memoria RAM e li ricodifica da zero** nel nuovo formato con algoritmi dedicati.

🌐 **Sito Web Vetrina Ufficiale**: Incluso nella cartella [`docs/index.html`](docs/index.html) (pronto per **GitHub Pages** con simulatore interattivo!).

---

## 🚀 Architettura dei 4 Motori Reali

| Categoria | Motore Reale Utilizzato | Cosa avviene realmente "Sotto il Cofano" | Formati Supportati |
| :--- | :--- | :--- | :--- |
| **🖼️ Immagini** | **Pillow + pillow-heif** | Decodifica la matrice di pixel grezzi, gestisce la trasparenza (compositing Alpha-Blending da RGBA a RGB per JPEG/BMP senza canale alfa), genera frame multi-risoluzione per le icone ICO e ricomprime con quantizzazione mirata. Supporta foto HEIC Apple/Samsung. | **PNG, JPG, WEBP, BMP, ICO, TIFF, GIF, PDF, HEIC, HEIF** |
| **🎬 Audio & Video** | **FFmpeg Core (Subprocess)** | Demultiplexa i contenitori multimediali (Atom MP4, EBML MKV/WebM), decodifica i flussi elementari con i codec nativi (H.264, VP9, AAC, LAME) e li ricodifica nei codec target con monitoraggio in tempo reale del tempo trascorso. Palettegen a 2 passaggi per GIF. | **MP4, MKV, AVI, MOV, WEBM, MP3, WAV, FLAC, OGG, AAC, GIF** |
| **📊 Dati & Tabelle** | **pandas + openpyxl** | Esegue il parsing sintattico della struttura tabellare, valida i tipi di dato per colonna istanziando un DataFrame relazionale in RAM e rigenera la serializzazione nativa (inclusa la struttura zip OpenXML per Excel con celle formattate). | **CSV, XLSX, JSON, HTML, XML, TSV** |
| **📄 Documenti** | **pdf2docx + docx2pdf + PyMuPDF + ReportLab** | Ispeziona i flussi vettoriali e i glifi tipografici di una pagina PDF, calcola i margini e le coordinate delle tabelle e ricostruisce l'albero XML WordprocessingML nativo con stili conformi. Renderizza inoltre pagine PDF a 300 DPI in immagini. | **PDF ➔ DOCX, DOCX ➔ PDF, PDF ➔ PNG/JPG, PDF ➔ TXT, TXT ➔ PDF** |

---

## 🎒 Portabilità Totale & Multipiattaforma (Windows, macOS, Linux)

Questo convertitore è progettato per essere **immediatamente utilizzabile su qualsiasi sistema**:
1. **Pronto all'uso su PC con solo Python standard**: se aperto su una macchina con una nuova installazione di Python priva di librerie esterne, si avvia un **bootstrapper grafico nativo** (usando solo il modulo integrato `tkinter`), consentendo all'utente di preparare tutti i motori con un solo clic.
2. **FFmpeg Portatile 1-Click Multi-Architettura**:
   - **Windows:** scarica le build ufficiali statiche di Gyan.dev / BtbN in `bin/ffmpeg.exe`.
   - **macOS:** rileva Homebrew su Apple Silicon (`/opt/homebrew/bin/ffmpeg`) o scarica la build universale ARM64/Intel.
   - **Linux:** rileva FFmpeg di sistema o scarica il binario statico autonomo `bin/ffmpeg` impostando i permessi `chmod +x`.
   - Nessun bisogno di permessi di amministratore o di modificare il `PATH` di sistema.
3. **LibreOffice Headless su Linux/macOS:** se presente su distribuzioni Linux o Mac privi di MS Office, converte al volo file DOCX in PDF con fedeltà tipografica nativa.
4. **Leggero di RAM (< 40 MB)**: elabora i file in sequenza tramite una coda asincrona multithread senza picchi di memoria.

---

## 🖥️ Come Avviarlo

### 🪟 Su Windows:
Fai doppio clic su:
```cmd
run.bat
```
*(Oppure da terminale PowerShell: `python main.py`)*

### 🍎 Su macOS (Apple Silicon M1/M2/M3/M4 & Intel):
Apri il Terminale nella cartella del programma ed esegui:
```bash
chmod +x run.sh
./run.sh
```

### 🐧 Su Linux (Ubuntu, Debian, Fedora, Arch):
Apri il terminale ed esegui:
```bash
chmod +x run.sh
./run.sh
```

---

## 🛡️ Sicurezza & Audit Double-Check

Il software è stato sottoposto a un'approfondita revisione di sicurezza:
- ✅ **Nessuna iniezione di comandi (Command Injection):** tutti i comandi di sistema (`ffmpeg`, `explorer`, `open`, `xdg-open`) vengono eseguiti tramite liste di argomenti separate con `shell=False`.
- ✅ **Protezione anti-sovrascrittura:** se file sorgente e destinazione coincidono nello stesso percorso, viene generato automaticamente un suffisso di sicurezza (`_converted`), preservando sempre il file originale.
- ✅ **Sanitizzazione estensioni:** prevenuto qualsiasi attacco di tipo *Path Traversal* (`../`).
- ✅ **Protezione Decompression Bomb (DoS):** gestione rigorosa delle matrici di pixel per scongiurare attacchi di esaurimento memoria tramite file immagine artefatti.
- ✅ **Protezione XXE (XML External Entity):** disabilitata l'inclusione di entità esterne nei file XML.
- ✅ **100% Locale e Privato:** nessun file inviato a server cloud terzi.

---

## 📁 Struttura del Progetto

```
Convertitore/
├── run.bat                     # Launcher rapido per Windows
├── run.sh                      # Launcher nativo per macOS e Linux
├── main.py                     # Entry point con Bootstrapper grafico Tkinter
├── requirements.txt            # Dipendenze dei motori di conversione
├── README.md                   # Documentazione completa
├── docs/                       # Sito Web vetrina per GitHub Pages
│   └── index.html              # Landing page interattiva con simulatore live
├── bin/                        # Directory riservata per ffmpeg portatile
├── core/
│   ├── format_registry.py      # Matrice di compatibilità e spiegazioni tecniche
│   ├── ffmpeg_manager.py       # Rilevamento e downloader multi-OS di FFmpeg
│   ├── dep_checker.py          # Verifica componenti e installatore pip
│   └── orchestrator.py         # Coda asincrona multithread con collision prevention
├── engines/
│   ├── image_engine.py         # Pillow + HEIF (Alpha-blending & safe-bomb)
│   ├── media_engine.py         # FFmpeg Subprocess con streaming stderr
│   ├── data_engine.py          # Pandas + OpenPyXL + pure Python fallback
│   └── doc_engine.py           # pdf2docx + docx2pdf + PyMuPDF + LibreOffice/ReportLab
└── gui/
    ├── app.py                  # Interfaccia Convertio Dark Mode
    ├── file_card.py            # Card interattiva multi-OS (Finder/Explorer/XDG)
    ├── explain_modal.py        # Spiegazione dettagliata della pipeline binaria
    ├── options_modal.py        # Opzioni di compressione, qualità e bitrate
    └── setup_dialog.py         # Gestore componenti e download 1-click FFmpeg
```

---
