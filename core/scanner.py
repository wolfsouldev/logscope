# core/scanner.py — Motor de escaneo de logs en disco

import re
from pathlib import Path
from datetime import date
from typing import Optional
from dataclasses import dataclass, field

from core.utils import (
    classify_log_file,
    get_file_date,
    get_file_size,
    has_content,
    can_read,
)


@dataclass
class LogFile:
    """Representa un archivo de log individual."""
    path: Path
    kind: str          # active | compressed | numbered | dated
    file_date: Optional[date]
    size_bytes: int
    readable: bool

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def is_compressed(self) -> bool:
        return self.kind == "compressed"


@dataclass
class ScanResult:
    """Resultado completo del escaneo de un directorio/servicio."""
    service_name: str
    base_path: Path
    found: bool
    readable: bool
    log_files: list = field(default_factory=list)
    error: Optional[str] = None

    # ─── Propiedades computadas ───────────────────────────────────────────

    @property
    def total_files(self) -> int:
        return len(self.log_files)

    @property
    def active_files(self) -> list:
        return [f for f in self.log_files if f.kind == "active"]

    @property
    def rotated_files(self) -> list:
        return [f for f in self.log_files if f.kind != "active"]

    @property
    def compressed_files(self) -> list:
        return [f for f in self.log_files if f.kind == "compressed"]

    @property
    def uncompressed_rotated(self) -> list:
        return [f for f in self.log_files if f.kind in ("numbered", "dated")]

    @property
    def total_size(self) -> int:
        return sum(f.size_bytes for f in self.log_files)

    @property
    def oldest_date(self) -> Optional[date]:
        dates = [f.file_date for f in self.log_files if f.file_date]
        return min(dates) if dates else None

    @property
    def newest_date(self) -> Optional[date]:
        dates = [f.file_date for f in self.log_files if f.file_date]
        return max(dates) if dates else None

    @property
    def coverage_days(self) -> Optional[int]:
        if self.oldest_date and self.newest_date:
            return (self.newest_date - self.oldest_date).days + 1
        return None

    @property
    def dual_rotation(self) -> bool:
        """
        True si hay mezcla de rotación por número y por fecha.
        Los comprimidos con fecha en el nombre cuentan como rotación por fecha.
        """
        _DATE_RE = re.compile(r"\d{4}[-]?\d{2}[-]?\d{2}")
        has_numbered = any(f.kind == "numbered" for f in self.log_files)
        has_dated = any(
            f.kind == "dated" or (f.kind == "compressed" and _DATE_RE.search(f.name))
            for f in self.log_files
        )
        return has_numbered and has_dated

    @property
    def no_rotation_detected(self) -> bool:
        """True si solo hay archivos activos, sin ninguna rotación."""
        return len(self.log_files) > 0 and all(
            f.kind == "active" for f in self.log_files
        )

    @property
    def uncompressed_rotated_size(self) -> int:
        return sum(f.size_bytes for f in self.uncompressed_rotated)


# ─── Clasificación de archivos de timestamp en nombre ───────────────────────
#
# AdGuard y otros servicios usan nombres como:
#   adguarddns-2026-05-02T15-24-44.038.log
#
# Para estos archivos, el "activo" es el que NO tiene timestamp
# (adguarddns.log) y los demás son rotados por fecha.

TIMESTAMP_IN_NAME_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}"  # 2026-05-02T15-24-44
)


def _classify_prefixed_file(path: Path, prefix: str) -> str:
    """
    Clasifica archivos con nombre basado en prefijo + timestamp.
    Ej: "adguarddns.log" → active
        "adguarddns-2026-05-02T15-24-44.038.log" → dated
    """
    name = path.name
    # Si tiene timestamp en el nombre → rotado por fecha
    if TIMESTAMP_IN_NAME_RE.search(name):
        return "dated"
    # Si termina en sufijo numérico → numbered
    if re.search(r"\.\d+$", name):
        return "numbered"
    # Si está comprimido
    if any(name.endswith(ext) for ext in (".gz", ".bz2", ".xz", ".zst")):
        return "compressed"
    # Nombre limpio con el prefijo → activo
    return "active"


# ─── Matching de archivos ────────────────────────────────────────────────────

def _matches_prefix(name: str, prefix: str) -> bool:
    """True si el nombre de archivo empieza por el prefijo dado."""
    return name.startswith(prefix)


def _matches_patterns(path: Path, patterns: list) -> bool:
    """True si el archivo coincide con alguno de los patrones."""
    name = path.name
    for pat in patterns:
        base = pat.replace("*", "")
        if base and base in name:
            return True
        if name == pat:
            return True
    return False


def _should_include(path: Path, log_prefix: str, log_patterns: list) -> bool:
    """
    Decide si un archivo debe incluirse en el escaneo.
    Acepta si coincide con el prefijo O con los patrones.
    """
    if log_prefix and _matches_prefix(path.name, log_prefix):
        return True
    if log_patterns and _matches_patterns(path, log_patterns):
        return True
    return False


# ─── Funciones públicas de escaneo ──────────────────────────────────────────

def scan_directory(
    service_name: str,
    base_path: Path,
    log_patterns: list,
    log_prefix: str = "",
    recursive: bool = False,
) -> ScanResult:
    """
    Escanea un directorio buscando archivos de log.

    Si log_prefix está definido, incluye todos los archivos cuyo nombre
    empiece con ese prefijo. Si log_patterns está definido, incluye los
    que coincidan con esos patrones. Ambos pueden usarse a la vez.

    Args:
        service_name: Nombre del servicio (para el resultado).
        base_path:    Directorio raíz donde buscar.
        log_patterns: Patrones de nombre exacto (ej: ["access.log"]).
        log_prefix:   Prefijo de nombre (ej: "adguarddns"). Vacío = ignorar.
        recursive:    Si True, busca también en subdirectorios.
    """
    if not base_path.exists():
        return ScanResult(
            service_name=service_name,
            base_path=base_path,
            found=False,
            readable=False,
            error=f"Ruta no encontrada: {base_path}",
        )

    if not can_read(base_path):
        return ScanResult(
            service_name=service_name,
            base_path=base_path,
            found=True,
            readable=False,
            error=f"Sin permisos de lectura en: {base_path}",
        )

    result = ScanResult(
        service_name=service_name,
        base_path=base_path,
        found=True,
        readable=True,
    )

    glob_fn = base_path.rglob if recursive else base_path.glob
    candidates = sorted(glob_fn("*"))

    for path in candidates:
        if not path.is_file():
            continue

        if not _should_include(path, log_prefix, log_patterns):
            continue

        # Ignorar archivos vacíos o sin contenido real —
        # su mtime contaminaría el rango de fechas sin aportar datos
        if not has_content(path):
            continue

        # Clasificación: usar lógica de prefijo si corresponde
        if log_prefix and _matches_prefix(path.name, log_prefix):
            kind = _classify_prefixed_file(path, log_prefix)
        else:
            from core.utils import classify_log_file
            kind = classify_log_file(path)

        file_date = get_file_date(path)
        size = get_file_size(path)
        readable = can_read(path)

        result.log_files.append(
            LogFile(
                path=path,
                kind=kind,
                file_date=file_date,
                size_bytes=size,
                readable=readable,
            )
        )

    return result


def scan_single_file(service_name: str, file_path: Path) -> ScanResult:
    """
    Crea un ScanResult para un único archivo de log (path es fichero, no dir).
    Ejemplo: /var/log/pihole.log
    """
    if not file_path.exists():
        return ScanResult(
            service_name=service_name,
            base_path=file_path.parent,
            found=False,
            readable=False,
            error=f"Archivo no encontrado: {file_path}",
        )

    readable = can_read(file_path)

    if not has_content(file_path):
        return ScanResult(
            service_name=service_name,
            base_path=file_path.parent,
            found=True,
            readable=readable,
            error=f"El archivo existe pero está vacío: {file_path.name}",
        )

    from core.utils import classify_log_file
    kind = classify_log_file(file_path)
    file_date = get_file_date(file_path)
    size = get_file_size(file_path)

    result = ScanResult(
        service_name=service_name,
        base_path=file_path.parent,
        found=True,
        readable=readable,
    )

    result.log_files.append(
        LogFile(
            path=file_path,
            kind=kind,
            file_date=file_date,
            size_bytes=size,
            readable=readable,
        )
    )

    return result
