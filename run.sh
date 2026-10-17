#!/usr/bin/env bash
# ========================================================
#       UNIVERSAL FILE CONVERTER - CONVERTITORE UNIVERSALE       
#       Launcher per macOS (Apple Silicon & Intel) & Linux
# ========================================================

set -e

# Posizionamento nella directory del programma
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================"
echo "      UNIVERSAL FILE CONVERTER - CONVERTITORE UNIVERSALE       "
echo "      macOS (Apple Silicon & Intel) & Linux             "
echo "========================================================"
echo ""
echo "Controllo ambiente Python in corso..."

# 1. Rilevamento interprete Python 3
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    # Verifica che sia effettivamente Python 3
    if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
        PY_CMD="python"
    fi
fi

if [ -z "$PY_CMD" ]; then
    echo ""
    echo "[ERRORE GRAVE] Python 3 non è stato trovato nel sistema."
    echo ""
    echo "Come installarlo:"
    echo "  - Su macOS (Homebrew): brew install python3"
    echo "  - Su macOS (Installer): https://www.python.org/downloads/"
    echo "  - Su Ubuntu/Debian:    sudo apt update && sudo apt install -y python3 python3-pip python3-tk"
    echo "  - Su Fedora:           sudo dnf install -y python3 python3-pip python3-tkinter"
    echo "  - Su Arch Linux:       sudo pacman -S python python-pip tk"
    echo ""
    exit 1
fi

echo "[OK] Python 3 rilevato: $($PY_CMD --version)"

# 2. Controllo supporto Tkinter per l'interfaccia grafica
if ! $PY_CMD -c "import tkinter" >/dev/null 2>&1; then
    echo ""
    echo "[!] AVVISO: Il modulo grafico 'tkinter' non è presente nella tua installazione Python."
    echo "Per visualizzare l'interfaccia, installalo rapidamente con il gestore del tuo sistema:"
    echo "  - Ubuntu / Debian: sudo apt install -y python3-tk"
    echo "  - Fedora:          sudo dnf install -y python3-tkinter"
    echo "  - Arch Linux:      sudo pacman -S tk"
    echo ""
    read -p "Vuoi tentare comunque l'avvio? (s/N): " choice
    case "$choice" in 
      s|S|y|Y ) echo "Continuo...";;
      * ) exit 1;;
    esac
fi

# 3. Avvio dell'applicazione
echo ""
echo "Avvio di Universal File Converter..."
exec "$PY_CMD" main.py "$@"
