# services/custom.py — Analizador para rutas personalizadas

from pathlib import Path

from core.parser import ServiceAnalyzer
from core.scanner import ScanResult, scan_directory, scan_single_file


class CustomAnalyzer(ServiceAnalyzer):

    name = "custom"
    label = "Ruta personalizada"
    default_paths = []
    log_patterns = ["*.log"]

    def detect(self) -> list[Path]:
        # No hay detección automática para rutas personalizadas
        return []

    def _scan(self, path: Path) -> ScanResult:
        if path.is_file():
            return scan_single_file(self.name, path)

        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
        )
