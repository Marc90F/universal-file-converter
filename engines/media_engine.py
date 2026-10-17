"""
Motore Audio/Video basato su FFmpeg.
Demultiplexa i contenitori multimediali, decodifica gli stream audio/video
e li ricodifica con i codec target (H.264, AAC, MP3, Vorbis, VP9, PCM, FLAC).
Include monitoraggio in tempo reale del progresso leggendo lo stream stderr di FFmpeg.
"""

import os
import re
import subprocess
from typing import Dict, Any, Callable, Optional
from core.ffmpeg_manager import find_ffmpeg, get_startupinfo, get_media_info

def convert_media(
    src_path: str,
    dst_path: str,
    options: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None
) -> Dict[str, Any]:
    """
    Esegue la conversione multimediale reale tramite FFmpeg subprocess.
    """
    ffmpeg_exe = find_ffmpeg()
    if not ffmpeg_exe:
        raise RuntimeError("FFmpeg non è installato o configurato. Usa il pulsante 'Installa FFmpeg' per scaricarlo in modo portatile.")

    options = options or {}
    audio_bitrate = str(options.get("audio_bitrate", "192k"))
    video_quality = options.get("video_quality", "medium") # high, medium, low
    resolution = options.get("resolution", "original")      # original, 1080p, 720p, 480p

    src_ext = os.path.splitext(src_path)[1].lower().lstrip(".")
    dst_ext = os.path.splitext(dst_path)[1].lower().lstrip(".")

    # Estrai durata del file sorgente per calcolare la percentuale esatta
    media_info = get_media_info(src_path)
    total_sec = media_info.get("duration_sec", 0.0)

    if progress_callback:
        progress_callback(5, f"Analisi flussi: {media_info.get('video_codec', 'N/D')} / {media_info.get('audio_codec', 'N/D')}...")

    # Mappatura CRF per qualità video
    crf_map = {"high": "18", "medium": "23", "low": "28"}
    crf = crf_map.get(video_quality, "23")

    # Costruzione argomenti FFmpeg
    cmd = [ffmpeg_exe, "-y", "-i", src_path]

    # Filtri video opzionali
    vf_filters = []
    if resolution == "1080p":
        vf_filters.append("scale=-2:1080")
    elif resolution == "720p":
        vf_filters.append("scale=-2:720")
    elif resolution == "480p":
        vf_filters.append("scale=-2:480")

    # 1. Destinazione: Formato Audio (estrazione o transcodifica audio)
    audio_formats = ("mp3", "wav", "flac", "ogg", "aac", "m4a", "opus")
    if dst_ext in audio_formats:
        cmd.extend(["-vn"]) # Rimuovi video

        if dst_ext == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", audio_bitrate])
        elif dst_ext == "wav":
            cmd.extend(["-c:a", "pcm_s16le", "-ar", "44100"])
        elif dst_ext == "flac":
            cmd.extend(["-c:a", "flac"])
        elif dst_ext == "aac":
            cmd.extend(["-c:a", "aac", "-b:a", audio_bitrate])
        elif dst_ext == "ogg":
            cmd.extend(["-c:a", "libvorbis", "-q:a", "6"])
        elif dst_ext == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", audio_bitrate])
        elif dst_ext == "opus":
            cmd.extend(["-c:a", "libopus", "-b:a", "128k"])

    # 2. Destinazione: GIF animata da video
    elif dst_ext == "gif":
        filter_str = "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        cmd.extend(["-vf", filter_str])

    # 3. Destinazione: Formato Video
    else:
        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        if dst_ext == "mp4":
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", crf,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", audio_bitrate
            ])
        elif dst_ext == "mkv":
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", crf,
                "-c:a", "aac",
                "-b:a", audio_bitrate
            ])
        elif dst_ext == "webm":
            cmd.extend([
                "-c:v", "libvpx-vp9",
                "-crf", "32",
                "-b:v", "0",
                "-c:a", "libopus",
                "-b:a", "128k"
            ])
        elif dst_ext == "avi":
            cmd.extend([
                "-c:v", "libxvid",
                "-qscale:v", "3",
                "-c:a", "libmp3lame",
                "-b:a", audio_bitrate
            ])
        elif dst_ext == "mov":
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", crf,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", audio_bitrate
            ])
        else:
            # Fallback generico
            cmd.extend(["-c:v", "libx264", "-c:a", "aac"])

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    cmd.append(dst_path)

    # Avvio processo con streaming di stderr
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=get_startupinfo()
    )

    time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d+)")

    while True:
        if is_cancelled and is_cancelled():
            process.kill()
            if os.path.exists(dst_path):
                os.remove(dst_path)
            raise RuntimeError("Conversione annullata dall'utente.")

        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break

        # Cerca timestamp corrente nel log di FFmpeg
        match = time_pattern.search(line)
        if match and total_sec > 0:
            h = float(match.group(1))
            m = float(match.group(2))
            s = float(match.group(3))
            current_sec = h * 3600 + m * 60 + s
            percent = min(98, max(5, int((current_sec / total_sec) * 100)))
            cur_time_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            tot_time_str = media_info.get("duration", "N/D")
            if progress_callback:
                progress_callback(percent, f"Ricodifica stream: {percent}% ({cur_time_str} / {tot_time_str})")

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg ha restituito codice di errore {process.returncode}. Verifica che il codec sorgente sia supportato.")

    if progress_callback:
        progress_callback(100, f"Conversione multimediale completata: {os.path.basename(dst_path)}")

    orig_bytes = os.path.getsize(src_path)
    new_bytes = os.path.getsize(dst_path) if os.path.exists(dst_path) else 0

    return {
        "status": "success",
        "src": src_path,
        "dst": dst_path,
        "orig_bytes": orig_bytes,
        "new_bytes": new_bytes,
        "media_info": media_info
    }
