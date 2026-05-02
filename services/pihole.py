# services/pihole.py — Analizador de logs de Pi-hole

from pathlib import Path

from core.parser import ServiceAnalyzer
from core.scanner import ScanResult, scan_directory, scan_single_file
from core.utils import find_existing_paths


class PiholeAnalyzer(ServiceAnalyzer):

    name = "pihole"
    label = "Pi-hole"

    default_paths = [
        "/var/log/pihole",
        "/var/log/pihole.log",   # instalaciones antiguas usan un único archivo
    ]

    log_patterns = [
        "pihole.log",
        "FTL.log",
        "pihole-FTL.log",
        "query.log",
    ]

    def _scan(self, path: Path) -> ScanResult:
        if path.is_file():
            return scan_single_file(self.name, path)

        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
        )

    def extra_diagnostics(self, result: ScanResult) -> list[str]:
        msgs = []
        names = [f.name for f in result.log_files]

        if not any("FTL" in n for n in names):
            msgs.append(
                "No se detecta pihole-FTL.log — "
                "¿está corriendo el servicio FTL?"
            )

        return msgs
