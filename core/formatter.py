# core/formatter.py — Presentación visual con Rich

from datetime import date
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from core.scanner import ScanResult
from core.utils import format_size
from config import THEME

console = Console()


# ─── Helpers ────────────────────────────────────────────────────────────────

def _fmt_date(d: Optional[date]) -> str:
    return d.strftime("%Y-%m-%d") if d else "—"


def _status_icon(ok: bool) -> str:
    return "✓" if ok else "✗"


# ─── Cabecera de la app ──────────────────────────────────────────────────────

def print_banner():
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]logscope[/bold cyan]  [dim]v1.1.0[/dim]\n"
            "[dim]Analizador de logs de sistema[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


# ─── Resultado de análisis ───────────────────────────────────────────────────

def print_scan_result(result: ScanResult, service_label: str):
    """Imprime el resumen completo de un escaneo."""

    console.print()

    # ── Header del servicio ──────────────────────────────────────────────────
    status_color = "green" if result.found and result.readable else "red"
    status_text = "Encontrado" if result.found and result.readable else (
        "Sin permisos" if result.found else "No encontrado"
    )

    console.print(
        Panel(
            f"[bold]{service_label}[/bold]  "
            f"[{status_color}]{_status_icon(result.found and result.readable)} {status_text}[/{status_color}]\n"
            f"[dim]{result.base_path}[/dim]",
            border_style=status_color,
            padding=(0, 2),
        )
    )

    if result.error:
        console.print(f"  [bold red]✗ {result.error}[/bold red]")
        return

    if not result.log_files:
        console.print("  [yellow]⚠ No se encontraron archivos de log en la ruta[/yellow]")
        return

    console.print()

    # ── Tabla resumen temporal ───────────────────────────────────────────────
    temporal = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    temporal.add_column("Campo", style="dim", width=22)
    temporal.add_column("Valor", style="bold white")

    temporal.add_row("Primer log",   _fmt_date(result.oldest_date))
    temporal.add_row("Último log",   _fmt_date(result.newest_date))

    if result.coverage_days is not None:
        days = result.coverage_days
        coverage_str = f"{days} días"
        if days >= 365:
            coverage_str += f"  [green](~{days // 365} año{'s' if days // 365 > 1 else ''})[/green]"
        elif days >= 30:
            coverage_str += f"  [yellow](~{days // 30} mes{'es' if days // 30 > 1 else ''})[/yellow]"
        temporal.add_row("Cobertura", coverage_str)

    console.print(temporal)
    console.print()

    # ── Tabla de inventario ──────────────────────────────────────────────────
    inv = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    inv.add_column("Campo", style="dim", width=22)
    inv.add_column("Valor", style="bold white")

    inv.add_row("Logs activos",         str(len(result.active_files)))
    inv.add_row("Logs rotados",         str(len(result.rotated_files)))
    inv.add_row("  Comprimidos",        str(len(result.compressed_files)))
    inv.add_row("  Sin comprimir",      str(len(result.uncompressed_rotated)))
    inv.add_row("Total archivos",       str(result.total_files))

    console.print(inv)
    console.print()

    # ── Tabla de tamaño ──────────────────────────────────────────────────────
    size_t = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    size_t.add_column("Campo", style="dim", width=22)
    size_t.add_column("Valor", style="bold white")

    size_t.add_row("Tamaño total", format_size(result.total_size))

    if result.coverage_days and result.coverage_days > 0:
        daily_avg = result.total_size / result.coverage_days
        size_t.add_row("Promedio diario", format_size(int(daily_avg)))

    if result.uncompressed_rotated_size > 0:
        size_t.add_row(
            "Rotados sin comprimir",
            f"[yellow]{format_size(result.uncompressed_rotated_size)}[/yellow]"
        )

    console.print(size_t)
    console.print()

    # ── Diagnósticos ────────────────────────────────────────────────────────
    _print_diagnostics(result)


def _print_diagnostics(result: ScanResult):
    """Imprime alertas y diagnósticos basados en el resultado del escaneo."""
    issues = []
    ok_msgs = []

    # Retención
    if result.coverage_days:
        if result.coverage_days >= 360:
            ok_msgs.append(f"Retención anual detectada ({result.coverage_days} días)")
        elif result.coverage_days >= 60:
            ok_msgs.append(f"Retención de {result.coverage_days} días detectada")
        else:
            issues.append(
                f"Retención corta: solo {result.coverage_days} días de logs"
            )

    # Rotación dual
    if result.dual_rotation:
        issues.append(
            "Rotación dual detectada — mezcla de rotación por número y por fecha"
        )

    # Sin rotación
    if result.no_rotation_detected and len(result.log_files) < 3:
        issues.append("No se detecta rotación — riesgo de logs sin límite de tamaño")

    # Logs sin comprimir acumulados
    if len(result.uncompressed_rotated) > 5:
        issues.append(
            f"{len(result.uncompressed_rotated)} logs rotados sin comprimir "
            f"({format_size(result.uncompressed_rotated_size)})"
        )

    # ── Imprimir ────────────────────────────────────────────────────────────
    for msg in ok_msgs:
        console.print(f"  [bold green]✓[/bold green] {msg}")

    for msg in issues:
        console.print(f"  [bold yellow]⚠[/bold yellow]  {msg}")

    if not issues and not ok_msgs:
        console.print("  [dim]Sin diagnósticos adicionales[/dim]")

    console.print()


# ─── Separadores y mensajes generales ───────────────────────────────────────

def print_section(title: str):
    console.rule(f"[bold cyan]{title}[/bold cyan]")
    console.print()


def print_error(msg: str):
    console.print(f"\n[bold red]✗ {msg}[/bold red]\n")


def print_info(msg: str):
    console.print(f"[dim]{msg}[/dim]")


def print_warning(msg: str):
    console.print(f"[bold yellow]⚠  {msg}[/bold yellow]")


def print_success(msg: str):
    console.print(f"[bold green]✓ {msg}[/bold green]")
