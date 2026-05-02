# services/nginx.py — Analizador de logs de Nginx

from pathlib import Path

from core.parser import ServiceAnalyzer
from core.scanner import ScanResult, scan_directory


class NginxAnalyzer(ServiceAnalyzer):

    name = "nginx"
    label = "Nginx"

    default_paths = [
        "/var/log/nginx",
    ]

    log_patterns = [
        "access.log",
        "error.log",
    ]

    def _scan(self, path: Path) -> ScanResult:
        # Nginx puede tener subdirectorios por virtualhost; escaneo recursivo
        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
            recursive=True,
        )

    def extra_diagnostics(self, result: ScanResult) -> list[str]:
        msgs = []
        names = [f.name for f in result.log_files]

        # Múltiples access.log → múltiples virtualhosts
        access_count = sum(1 for n in names if "access.log" in n)
        if access_count > 1:
            msgs.append(
                f"{access_count} archivos access.log detectados — "
                f"configuración multi-virtualhost"
            )

        return msgs
