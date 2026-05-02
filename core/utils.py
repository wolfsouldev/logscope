# core/utils.py — Utilidades compartidas

import os
import re
import gzip
import stat
from datetime import datetime, date
from pathlib import Path
from typing import Optional


# ─── Permisos ──────────────────────────────────────────────────────────────

def is_root() -> bool:
    """Comprueba si el proceso corre como root."""
    return os.geteuid() == 0


def can_read(path: Path) -> bool:
    """Comprueba si el path es legible."""
    try:
        return os.access(path, os.R_OK)
    except Exception:
        return False


# ─── Fechas ────────────────────────────────────────────────────────────────

# Patrones de fecha en nombres de archivo
DATE_PATTERNS = [
    (r"(\d{4})(\d{2})(\d{2})", "%Y%m%d"),       # 20260502
    (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),   # 2026-05-02
    (r"(\d{2})(\d{2})(\d{4})", "%d%m%Y"),        # 02052026
]

DATE_RE = [
    (re.compile(pat), fmt) for pat, fmt in DATE_PATTERNS
]


def extract_date_from_filename(name: str) -> Optional[date]:
    """Intenta extraer una fecha del nombre de archivo."""
    for pattern, fmt in DATE_RE:
        match = pattern.search(name)
        if match:
            try:
                date_str = match.group(0)
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
    return None


def get_file_mtime(path: Path) -> Optional[date]:
    """Devuelve la fecha de modificación de un archivo."""
    try:
        return date.fromtimestamp(path.stat().st_mtime)
    except Exception:
        return None


def get_file_date(path: Path) -> Optional[date]:
    """Obtiene la fecha más fiable de un archivo (nombre > mtime)."""
    d = extract_date_from_filename(path.name)
    if d:
        return d
    return get_file_mtime(path)


# ─── Tamaños ───────────────────────────────────────────────────────────────

def format_size(size_bytes: int) -> str:
    """Formatea bytes a unidad legible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024**3:.2f} GB"


# Tamaño mínimo para considerar un archivo con datos reales (evita archivos vacíos/placeholder)
MIN_LOG_BYTES = 10


def get_file_size(path: Path) -> int:
    """
    Devuelve el tamaño REAL en disco del archivo.
    Para .gz reportamos el tamaño comprimido (lo que ocupa en disco),
    no el descomprimido — el objetivo es saber cuánto espacio consume.
    """
    try:
        return path.stat().st_size
    except Exception:
        return 0


def has_content(path: Path) -> bool:
    """True si el archivo tiene datos reales (no está vacío ni es un placeholder)."""
    try:
        return path.stat().st_size >= MIN_LOG_BYTES
    except Exception:
        return False


# ─── Clasificación de archivos ─────────────────────────────────────────────

COMPRESSED_EXTS = {".gz", ".bz2", ".xz", ".zst"}
NUMBERED_RE = re.compile(r"\.\d+$")
DATED_RE = re.compile(r"\d{4}[-]?\d{2}[-]?\d{2}")


def classify_log_file(path: Path) -> str:
    """
    Clasifica un archivo de log como:
    - 'active'     → sin extensión de rotación
    - 'compressed' → .gz, .bz2, etc.
    - 'numbered'   → .1, .2, ...
    - 'dated'      → contiene fecha en el nombre
    """
    name = path.name
    suffixes = path.suffixes

    if any(s in COMPRESSED_EXTS for s in suffixes):
        return "compressed"
    if NUMBERED_RE.search(name) and not DATED_RE.search(name):
        return "numbered"
    if DATED_RE.search(name):
        return "dated"
    return "active"


# ─── Paths ─────────────────────────────────────────────────────────────────

def resolve_path(raw: str) -> Optional[Path]:
    """Resuelve y valida un path introducido por el usuario."""
    p = Path(raw.strip()).expanduser().resolve()
    return p if p.exists() else None


def find_existing_paths(candidates: list[str]) -> list[Path]:
    """De una lista de rutas candidatas, devuelve las que existen."""
    result = []
    for c in candidates:
        p = Path(c)
        if p.exists():
            result.append(p)
    return result
