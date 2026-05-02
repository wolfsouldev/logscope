#!/usr/bin/env python3
# main.py — Punto de entrada de logscope v1.1

import sys
from pathlib import Path
from typing import Optional

try:
    import questionary
    from questionary import Style
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

from rich.console import Console

from config import (
    ServiceConfig, VERSION,
    load_services, add_service, get_service,
)
from core.formatter import (
    console,
    print_banner,
    print_scan_result,
    print_section,
    print_error,
    print_warning,
    print_info,
    print_success,
)
from core.parser import ServiceAnalyzer
from core.utils import is_root, resolve_path

# ─── Estilo questionary ──────────────────────────────────────────────────────

Q_STYLE = Style([
    ("qmark",       "fg:#00bcd4 bold"),
    ("question",    "bold"),
    ("answer",      "fg:#00e676 bold"),
    ("pointer",     "fg:#00bcd4 bold"),
    ("highlighted", "fg:#00e676 bold"),
    ("selected",    "fg:#00e676"),
    ("separator",   "fg:#555555"),
    ("instruction", "fg:#888888"),
    ("text",        ""),
    ("disabled",    "fg:#555555 italic"),
])


# ─── Selector de servicio ────────────────────────────────────────────────────

def choose_service() -> Optional[ServiceConfig]:
    """Muestra el selector interactivo. Devuelve el ServiceConfig elegido."""
    services = load_services()

    if HAS_QUESTIONARY:
        choices = []
        for svc in services:
            choices.append(questionary.Choice(title=svc.label, value=svc))
        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="➕  Agregar servicio", value="__add__"))
        choices.append(questionary.Choice(title="Salir", value=None))

        result = questionary.select(
            "Selecciona un servicio:",
            choices=choices,
            style=Q_STYLE,
            instruction="(↑↓ navegar, Enter seleccionar)",
        ).ask()
    else:
        console.print("\n[bold]Servicios disponibles:[/bold]\n")
        for i, svc in enumerate(services, 1):
            console.print(f"  [{i}] {svc.label}")
        console.print(f"  [A] Agregar servicio")
        console.print(f"  [0] Salir\n")
        raw = input("Selección: ").strip().lower()
        if raw == "0":
            return None
        if raw == "a":
            return "__add__"
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(services):
                result = services[idx]
            else:
                result = None
        except ValueError:
            result = None

    return result


# ─── Confirmar / editar ruta ─────────────────────────────────────────────────

def confirm_path(detected: list, svc: ServiceConfig) -> Optional[Path]:
    """
    Muestra las rutas detectadas y permite al usuario elegir o cambiar.
    """
    if not detected:
        console.print(f"  [yellow]No se detectó ninguna ruta automática.[/yellow]")
        return ask_custom_path()

    path = detected[0]

    if HAS_QUESTIONARY:
        action = questionary.select(
            f"Ruta detectada:",
            choices=[
                questionary.Choice(f"✓  Usar:  {path}", value="use"),
                questionary.Choice("✎  Introducir otra ruta", value="custom"),
                questionary.Choice("✗  Cancelar", value=None),
            ],
            style=Q_STYLE,
        ).ask()
    else:
        console.print(f"\n  Ruta detectada: [bold]{path}[/bold]")
        console.print("  [U] Usar  |  [N] Otra  |  [C] Cancelar")
        raw = input("  Opción: ").strip().lower()
        action = "use" if raw == "u" else ("custom" if raw == "n" else None)

    if action == "use":
        return path
    elif action == "custom":
        return ask_custom_path()
    return None


def ask_custom_path() -> Optional[Path]:
    if HAS_QUESTIONARY:
        raw = questionary.path(
            "Ruta al directorio/archivo de logs:",
            style=Q_STYLE,
        ).ask()
    else:
        raw = input("  Ruta: ").strip()

    if not raw:
        return None
    path = resolve_path(raw)
    if path is None:
        print_error(f"La ruta '{raw}' no existe")
        return None
    return path


# ─── Confirmar / editar prefijo ──────────────────────────────────────────────

def confirm_prefix(svc: ServiceConfig) -> str:
    """
    Muestra el prefijo por defecto del servicio y permite al usuario
    confirmarlo, cambiarlo o dejarlo vacío.

    Devuelve el prefijo final a usar (puede ser "").
    """
    default = svc.log_prefix

    default_label = f'"{default}"' if default else '(ninguno)'
    console.print(f"  Prefijo por defecto: [bold]{default_label}[/bold]")

    if HAS_QUESTIONARY:
        action = questionary.select(
            "¿Qué prefijo usar?",
            choices=[
                questionary.Choice(
                    f'✓  Usar: "{default}"' if default else '✓  Sin prefijo',
                    value="use"
                ),
                questionary.Choice("✎  Introducir prefijo personalizado", value="custom"),
                questionary.Choice("✗  Sin prefijo (buscar por patrones)", value="none"),
            ],
            style=Q_STYLE,
        ).ask()
    else:
        console.print("  [U] Usar  |  [N] Personalizar  |  [X] Sin prefijo")
        raw = input("  Opción: ").strip().lower()
        action = "use" if raw == "u" else ("custom" if raw == "n" else "none")

    if action == "use":
        return default
    elif action == "none":
        return ""
    else:
        if HAS_QUESTIONARY:
            new = questionary.text(
                "Prefijo de búsqueda (ej: adguarddns):",
                style=Q_STYLE,
            ).ask()
        else:
            new = input("  Prefijo: ").strip()
        return (new or "").strip()


# ─── Agregar servicio nuevo ──────────────────────────────────────────────────

def wizard_add_service():
    """Asistente para añadir un nuevo servicio a services.json."""
    print_section("Agregar nuevo servicio")
    console.print("[dim]Los datos se guardarán en services.json.[/dim]\n")

    def ask(prompt, default=""):
        if HAS_QUESTIONARY:
            return (questionary.text(prompt, default=default, style=Q_STYLE).ask() or "").strip()
        else:
            raw = input(f"  {prompt} [{default}]: ").strip()
            return raw if raw else default

    service_id = ask("ID interno (sin espacios, ej: haproxy)").lower().replace(" ", "_")
    if not service_id:
        print_error("ID no puede estar vacío")
        return

    label = ask("Nombre visible (ej: HAProxy)")
    if not label:
        label = service_id

    paths_raw = ask("Rutas de logs separadas por coma (ej: /var/log/haproxy,/var/log/haproxy.log)")
    paths = [p.strip() for p in paths_raw.split(",") if p.strip()]

    prefix = ask("Prefijo de archivos (ej: haproxy-, dejar vacío si no aplica)")

    patterns_raw = ask("Patrones de archivo separados por coma (ej: access.log,error.log)")
    patterns = [p.strip() for p in patterns_raw.split(",") if p.strip()]

    svc = ServiceConfig(
        id=service_id,
        label=label,
        paths=paths,
        log_prefix=prefix,
        log_patterns=patterns,
    )

    add_service(svc)
    print_success(f'Servicio "{label}" añadido a services.json')
    console.print("[dim]Disponible en el selector desde ahora.[/dim]\n")


# ─── Flujo principal de análisis ─────────────────────────────────────────────

def run_analysis(svc: ServiceConfig):
    print_section(f"Analizando {svc.label}")

    analyzer = ServiceAnalyzer(cfg=svc)

    # Detección automática de rutas
    if svc.id == "custom" or not svc.paths:
        path = ask_custom_path()
        if not path:
            return
        detected = [path]
    else:
        detected = analyzer.detect()

    # Confirmar ruta
    final_path = confirm_path(detected, svc)
    if final_path is None:
        print_info("Análisis cancelado.")
        return

    # Siempre preguntar por el prefijo antes de escanear
    final_prefix = confirm_prefix(svc)

    console.print(f"\n  [dim]Escaneando {final_path} ...[/dim]")
    if final_prefix:
        console.print(f"  [dim]Prefijo: {final_prefix}*[/dim]")

    # Aplicar prefijo elegido al analizador
    analyzer.log_prefix = final_prefix

    result = analyzer.analyze(final_path)

    print_scan_result(result, svc.label)

    extra = analyzer.extra_diagnostics(result)
    for msg in extra:
        console.print(f"  [bold cyan]ℹ[/bold cyan]  {msg}")
    if extra:
        console.print()


# ─── Permisos ────────────────────────────────────────────────────────────────

def check_permissions():
    if not is_root():
        print_warning(
            "No estás corriendo como root. "
            "Algunos logs requieren sudo para ser leídos."
        )
        console.print()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print_banner()
    check_permissions()

    if not HAS_QUESTIONARY:
        print_warning(
            "questionary no instalado — usando selector básico.\n"
            "  pip install questionary"
        )
        console.print()

    while True:
        choice = choose_service()

        if choice is None:
            console.print("\n[dim]Hasta luego.[/dim]\n")
            break

        if choice == "__add__":
            wizard_add_service()
            continue

        run_analysis(choice)

        if HAS_QUESTIONARY:
            again = questionary.confirm(
                "¿Analizar otro servicio?",
                default=True,
                style=Q_STYLE,
            ).ask()
            if not again:
                console.print("\n[dim]Hasta luego.[/dim]\n")
                break
        else:
            raw = input("¿Analizar otro servicio? [S/n]: ").strip().lower()
            if raw == "n":
                console.print("\n[dim]Hasta luego.[/dim]\n")
                break


if __name__ == "__main__":
    main()
