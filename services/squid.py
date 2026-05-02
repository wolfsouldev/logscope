# services/squid.py — Analizador de logs de Squid Proxy

from pathlib import Path

from core.parser import ServiceAnalyzer
from core.scanner import ScanResult, scan_directory
from core.utils import find_existing_paths


class SquidAnalyzer(ServiceAnalyzer):
    """
    Analizador para Squid Proxy.

    Rutas habituales:
      - /var/log/squid/        → instalación desde paquete (Debian/Ubuntu)
      - /var/log/squid3/       → versión antigua del paquete
      - /usr/local/squid/logs/ → compilación manual
    """

    name = "squid"
    label = "Squid Proxy"

    default_paths = [
        "/var/log/squid",
        "/var/log/squid3",
        "/usr/local/squid/logs",
        "/var/squid/logs",
    ]

    log_patterns = [
        "access.log",
        "error.log",
        "cache.log",
        "store.log",
    ]

    def _scan(self, path: Path) -> ScanResult:
        """
        Squid siempre escribe en un directorio, nunca en un único archivo.
        Forzamos scan_directory con los patrones conocidos.
        """
        return scan_directory(
            service_name=self.name,
            base_path=path,
            log_patterns=self.log_patterns,
        )

    def extra_diagnostics(self, result: ScanResult) -> list[str]:
        msgs = []

        # Squid puede generar access.log muy grande; avisar si activo > 500 MB
        for f in result.active_files:
            if f.size_bytes > 500 * 1024 * 1024:
                msgs.append(
                    f"access.log activo supera 500 MB ({f.size_bytes / 1024**2:.0f} MB) "
                    f"— considera forzar rotación"
                )

        # Si hay store.log pero no hay access.log, advertir
        names = [f.name for f in result.log_files]
        has_access = any("access.log" in n for n in names)
        has_store = any("store.log" in n for n in names)
        if has_store and not has_access:
            msgs.append(
                "store.log encontrado pero no access.log — "
                "¿está deshabilitado el log de acceso?"
            )

        return msgs
