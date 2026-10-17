"""
Gestore di FFmpeg multipiattaforma (Windows, macOS ARM/Intel, Linux).
- Rilevamento automatico di FFmpeg (PATH di sistema, bin/ locale, percorsi noti Unix/macOS/Windows).
- Download automatico 1-click della versione portable corretta per l'architettura corrente
  (Windows x64, macOS Apple Silicon M1/M2/M3/M4, macOS Intel x86_64, Linux x86_64 / ARM64).
- Estrazione metadati (durata, risoluzione, bitrate, codec) per mostrare anteprime guidate.
"""

import os
import sys
import shutil
import subprocess
import re
import platform
import zipfile
import tarfile
import urllib.request
from typing import Optional, Dict, Tuple, Callable

# Percorso base dell'applicazione
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_BIN_DIR = os.path.join(BASE_DIR, "bin")

def get_platform_info() -> Tuple[str, str, bool]:
    """Restituisce (sistema_operativo, architettura, is_arm)."""
    sys_name = platform.system().lower() # 'windows', 'darwin', 'linux'
    machine = platform.machine().lower() # 'amd64', 'x86_64', 'arm64', 'aarch64'
    is_arm = "arm" in machine or "aarch" in machine
    return sys_name, machine, is_arm

def get_startupinfo():
    """Restituisce uno STARTUPINFO per Windows per evitare che compaiano finestre nere CMD."""
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None

def find_ffmpeg() -> Optional[str]:
    """Cerca l'eseguibile di ffmpeg in ordine di priorità su Windows, macOS e Linux."""
    exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"

    # 1. Controlla nella cartella bin/ locale dell'applicazione
    local_ffmpeg = os.path.join(LOCAL_BIN_DIR, exe_name)
    if os.path.isfile(local_ffmpeg):
        return local_ffmpeg

    # 2. Controlla nella root dell'applicazione
    root_ffmpeg = os.path.join(BASE_DIR, exe_name)
    if os.path.isfile(root_ffmpeg):
        return root_ffmpeg

    # 3. Controlla nel PATH di sistema
    in_path = shutil.which("ffmpeg")
    if in_path:
        return in_path

    # 4. Controlla percorsi noti specifici per ciascun sistema operativo
    sys_name, _, is_arm = get_platform_info()
    common_paths = []

    if sys_name == "windows":
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"),
        ]
    elif sys_name == "darwin": # macOS
        if is_arm:
            # Percorso standard Homebrew su Apple Silicon (M1/M2/M3/M4)
            common_paths.append("/opt/homebrew/bin/ffmpeg")
        # Percorso standard Homebrew su Mac Intel o MacPorts
        common_paths.extend([
            "/usr/local/bin/ffmpeg",
            "/opt/local/bin/ffmpeg",
            "/usr/bin/ffmpeg"
        ])
    elif sys_name == "linux":
        common_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/snap/bin/ffmpeg",
            os.path.expanduser("~/.local/bin/ffmpeg")
        ]

    for p in common_paths:
        if os.path.isfile(p):
            return p

    return None

def find_ffprobe() -> Optional[str]:
    """Cerca l'eseguibile di ffprobe."""
    exe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"

    local_ffprobe = os.path.join(LOCAL_BIN_DIR, exe_name)
    if os.path.isfile(local_ffprobe):
        return local_ffprobe

    root_ffprobe = os.path.join(BASE_DIR, exe_name)
    if os.path.isfile(root_ffprobe):
        return root_ffprobe

    in_path = shutil.which("ffprobe")
    if in_path:
        return in_path

    # Su macOS Homebrew
    sys_name, _, is_arm = get_platform_info()
    if sys_name == "darwin":
        if is_arm and os.path.isfile("/opt/homebrew/bin/ffprobe"):
            return "/opt/homebrew/bin/ffprobe"
        if os.path.isfile("/usr/local/bin/ffprobe"):
            return "/usr/local/bin/ffprobe"
    elif sys_name == "linux" and os.path.isfile("/usr/bin/ffprobe"):
        return "/usr/bin/ffprobe"

    return None

def is_ffmpeg_available() -> bool:
    """Verifica se FFmpeg è pronto all'uso."""
    return find_ffmpeg() is not None

def download_portable_ffmpeg(progress_callback: Optional[Callable[[int, str], None]] = None) -> bool:
    """
    Scarica ed estrae la versione portable di FFmpeg corretta per il sistema corrente:
    - Windows: gyan.dev / BtbN build statiche
    - macOS (Apple Silicon ARM64 & Intel): evermeet.cx / eugeneware static build
    - Linux (x86_64 / ARM64): static release ufficiali
    Non richiede permessi di amministratore e rende l'app 100% autonoma.
    """
    os.makedirs(LOCAL_BIN_DIR, exist_ok=True)
    sys_name, _, is_arm = get_platform_info()
    exe_name = "ffmpeg.exe" if sys_name == "windows" else "ffmpeg"
    target_path = os.path.join(LOCAL_BIN_DIR, exe_name)

    # Definizione URL in base a OS e Architettura
    if sys_name == "windows":
        archive_name = "ffmpeg_temp.zip"
        urls = [
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        ]
        is_direct_binary = False
    elif sys_name == "darwin": # macOS
        archive_name = "ffmpeg_mac.zip"
        # Evermeet fornisce build universali/statiche per macOS
        urls = [
            "https://evermeet.cx/ffmpeg/getrelease/zip",
            "https://github.com/eugeneware/ffmpeg-static/releases/latest/download/ffmpeg-darwin-arm64" if is_arm else "https://github.com/eugeneware/ffmpeg-static/releases/latest/download/ffmpeg-darwin-x64"
        ]
        is_direct_binary = False
    else: # Linux
        archive_name = "ffmpeg_linux"
        # Linux static standalone binary
        arch_tag = "linux-arm64" if is_arm else "linux-x64"
        urls = [
            f"https://github.com/eugeneware/ffmpeg-static/releases/latest/download/ffmpeg-{arch_tag}"
        ]
        is_direct_binary = True

    if progress_callback:
        progress_callback(5, f"Inizializzazione download FFmpeg per {sys_name.capitalize()} ({'ARM' if is_arm else 'x86_64'})...")

    download_file = os.path.join(LOCAL_BIN_DIR, archive_name)
    downloaded = False

    for url in urls:
        try:
            if progress_callback:
                progress_callback(10, f"Connessione al server ({sys_name})...")

            def _reporthook(blocknum, blocksize, totalsize):
                if totalsize > 0 and progress_callback:
                    percent = min(80, int(15 + (blocknum * blocksize / totalsize) * 65))
                    mb_read = (blocknum * blocksize) / (1024 * 1024)
                    mb_total = totalsize / (1024 * 1024)
                    progress_callback(percent, f"Scaricamento: {mb_read:.1f} MB / {mb_total:.1f} MB ({percent}%)")

            # Se è un download diretto del binario (Linux)
            if url.endswith(f"-{arch_tag}" if sys_name == "linux" else "none"):
                urllib.request.urlretrieve(url, target_path, reporthook=_reporthook)
                os.chmod(target_path, 0o755)
                downloaded = True
                break

            urllib.request.urlretrieve(url, download_file, reporthook=_reporthook)
            downloaded = True
            break
        except Exception as e:
            if progress_callback:
                progress_callback(15, f"Mirror non disponibile ({e}), provo alternativo...")
            continue

    if not downloaded:
        if os.path.exists(download_file):
            os.remove(download_file)
        return False

    if is_direct_binary and os.path.isfile(target_path):
        os.chmod(target_path, 0o755)
        if progress_callback:
            progress_callback(100, "FFmpeg Portable pronto all'uso!")
        return True

    # Estrazione mirata per file zip (Windows e macOS)
    if progress_callback:
        progress_callback(85, "Estrazione del binario FFmpeg...")

    try:
        if zipfile.is_zipfile(download_file):
            with zipfile.ZipFile(download_file, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    filename = os.path.basename(member)
                    if filename.lower() in (exe_name.lower(), "ffprobe.exe", "ffprobe"):
                        cur_target = os.path.join(LOCAL_BIN_DIR, filename)
                        with zip_ref.open(member) as source, open(cur_target, "wb") as target:
                            shutil.copyfileobj(source, target)
                        # Imposta permessi eseguibili su macOS e Linux
                        if sys.platform != "win32":
                            os.chmod(cur_target, 0o755)

        if os.path.exists(download_file):
            os.remove(download_file)

        if progress_callback:
            progress_callback(100, "FFmpeg Portable pronto all'uso!")

        return os.path.isfile(target_path)
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"Errore estrazione: {e}")
        return False

def get_media_info(filepath: str) -> Dict[str, str]:
    """
    Ispeziona un file audio o video e restituisce metadati reali (durata, risoluzione, codec, bitrate).
    Funziona in modo identico e sicuro su Windows, macOS e Linux.
    """
    ffmpeg_exe = find_ffmpeg()
    if not ffmpeg_exe:
        return {"error": "FFmpeg non trovato"}

    info = {
        "duration": "N/D",
        "duration_sec": 0.0,
        "video_codec": "N/D",
        "audio_codec": "N/D",
        "resolution": "N/D",
        "bitrate": "N/D",
        "fps": "N/D"
    }

    try:
        cmd = [ffmpeg_exe, "-i", filepath]
        res = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=get_startupinfo()
        )
        output = res.stderr

        # Cerca durata
        dur_match = re.search(r"Duration:\s*(\d{2}:\d{2}:\d{2}\.\d+)", output)
        if dur_match:
            dur_str = dur_match.group(1)
            info["duration"] = dur_str.split(".")[0]
            parts = dur_str.split(":")
            info["duration_sec"] = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

        # Cerca bitrate
        br_match = re.search(r"bitrate:\s*(\d+\s*kb/s)", output)
        if br_match:
            info["bitrate"] = br_match.group(1)

        # Cerca stream video
        v_match = re.search(r"Stream #\d+:\d+.*Video:\s*([^,]+),.*?(\d{2,5}x\d{2,5})", output)
        if v_match:
            info["video_codec"] = v_match.group(1).strip()
            info["resolution"] = v_match.group(2).strip()

        # Cerca FPS
        fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", output)
        if fps_match:
            info["fps"] = fps_match.group(1)

        # Cerca stream audio
        a_match = re.search(r"Stream #\d+:\d+.*Audio:\s*([^,]+)", output)
        if a_match:
            info["audio_codec"] = a_match.group(1).strip()

    except Exception as e:
        info["error"] = str(e)

    return info
