# config.py — Configuración central de logscope

import json
from pathlib import Path
from dataclasses import dataclass

VERSION = "1.1.0"
APP_NAME = "logscope"

CONFIG_FILE = Path(__file__).parent / "services.json"


# ─── Modelo de servicio ──────────────────────────────────────────────────────

@dataclass
class ServiceConfig:
    id: str
    label: str
    paths: list
    log_prefix: str          # Prefijo de nombre de archivo (ej: "adguarddns")
    log_patterns: list       # Patrones exactos adicionales (ej: "access.log")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "paths": self.paths,
            "log_prefix": self.log_prefix,
            "log_patterns": self.log_patterns,
        }


# ─── Carga y guardado ────────────────────────────────────────────────────────

def load_services() -> list:
    """Carga los servicios desde services.json."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"No se encontró {CONFIG_FILE}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return [ServiceConfig(**entry) for entry in raw]


def save_services(services: list):
    """Guarda la lista de servicios en services.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump([s.to_dict() for s in services], f, indent=2, ensure_ascii=False)
        f.write("\n")


def get_service(service_id: str):
    """Devuelve la config de un servicio por su ID."""
    for svc in load_services():
        if svc.id == service_id:
            return svc
    return None


def add_service(svc: ServiceConfig):
    """Añade un nuevo servicio al archivo de configuración."""
    services = load_services()
    services = [s for s in services if s.id != svc.id]
    insert_idx = next(
        (i for i, s in enumerate(services) if s.id == "custom"),
        len(services)
    )
    services.insert(insert_idx, svc)
    save_services(services)


# ─── Colores para Rich ───────────────────────────────────────────────────────

THEME = {
    "title":     "bold cyan",
    "success":   "bold green",
    "warning":   "bold yellow",
    "error":     "bold red",
    "info":      "dim white",
    "highlight": "bold white",
    "muted":     "dim",
}
