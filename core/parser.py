# core/parser.py — Clase base para todos los analizadores de servicio

from pathlib import Path
from typing import Optional

from core.scanner import ScanResult, scan_directory, scan_single_file
from core.utils import find_existing_paths


class ServiceAnalyzer:
    """
    Clase base que heredan todos los analizadores de servicio.

    A partir de v1.1, recibe un ServiceConfig en lugar de tener
    los atributos hardcodeados, lo que permite crear analizadores
    para cualquier servicio definido en services.json.
    """

    def __init__(self, cfg=None):
        """
        cfg: ServiceConfig (de config.py). Si es None, usa los atributos
             de clase definidos por subclases legacy.
        """
        if cfg is not None:
            self._cfg = cfg
            self.name = cfg.id
            self.label = cfg.label
            self.default_paths = cfg.paths
            self.log_patterns = cfg.log_patterns
            self.log_prefix = cfg.log_prefix
        else:
            # Compatibilidad con subclases que definen atributos de clase
            self.log_prefix = getattr(self, "log_prefix", "")

    # ── API pública ──────────────────────────────────────────────────────────

    def detect(self) -> list:
        """
        Devuelve las rutas existentes de entre las rutas por defecto.
        """
        return find_existing_paths(self.default_paths)

    def analyze(self, path: Optional[Path] = None) -> ScanResult:
        """
        Punto de entrada principal.

        Args:
            path: Si se pasa, usa esa ruta. Si no, autodetecta.
        """
        if path is None:
            candidates = self.detect()
            if not candidates:
                fallback = self.default_paths[0] if self.default_paths else "/"
                return ScanResult(
                    service_name=self.name,
                    base_path=Path(fallback),
                    found=False,
                    readable=False,
                    error="No se encontró ninguna ruta de logs para este servicio",
                )
            path = candidates[0]

        return self._scan(path)

    # ── Métodos que las subclases pueden sobreescribir ───────────────────────

    def _scan(self, path: Path) -> ScanResult:
        """
        Escanea el path. Distingue archivo vs directorio.
        Sobreescribir para lógica especial.
        """
        if path.is_file():
            return scan_single_file(self.name, path)

        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
            log_prefix=self.log_prefix,
        )

    def extra_diagnostics(self, result: ScanResult) -> list:
        """
        Diagnósticos adicionales específicos del servicio.
        Sobreescribir en subclases para añadir checks propios.
        """
        return []
