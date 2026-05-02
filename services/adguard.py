# services/adguard.py — Analizador de logs de AdGuard Home

from pathlib import Path

from core.parser import ServiceAnalyzer
from core.scanner import ScanResult, scan_directory


class AdGuardAnalyzer(ServiceAnalyzer):

    name = "adguard"
    label = "AdGuard Home"

    default_paths = [
        "/opt/AdGuardHome/work",
        "/opt/AdGuardHome",
        "/var/lib/AdGuardHome",
        "/usr/local/AdGuardHome",
    ]

    log_patterns = [
        "querylog.json",
        "querylog.json.1",
        "data",
    ]

    def _scan(self, path: Path) -> ScanResult:
        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
        )

    def extra_diagnostics(self, result: ScanResult) -> list[str]:
        msgs = []

        if not result.log_files:
            msgs.append(
                "AdGuard Home usa querylog.json — "
                "si no aparece, verifica 'work_dir' en AdGuardHome.yaml"
            )

        return msgs
