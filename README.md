# logscope

Analizador interactivo de logs de sistema para Linux.

Detecta, clasifica y resume los logs de los servicios más comunes, con diagnósticos automáticos sobre retención, rotación y uso de disco.

---

## Servicios soportados

| Servicio      | Rutas por defecto                       |
|---------------|-----------------------------------------|
| Squid Proxy   | `/var/log/squid`, `/var/log/squid3`     |
| Nginx         | `/var/log/nginx`                        |
| Pi-hole       | `/var/log/pihole`, `/var/log/pihole.log`|
| AdGuard Home  | `/opt/AdGuardHome/work`                 |
| Ruta custom   | La que tú indiques                      |

---

## Instalación

```bash
git clone https://github.com/tu-usuario/logscope
cd logscope
pip install -r requirements.txt
```

---

## Uso

```bash
sudo python main.py
```

> Se recomienda `sudo` porque la mayoría de logs en `/var/log` requieren permisos de root.

---

## Salida de ejemplo

```
╭─────────────────────────────────╮
│  logscope  v1.0.0               │
│  Analizador de logs de sistema  │
╰─────────────────────────────────╯

╭─────────────────────────────────────────────╮
│  Squid Proxy  ✓ Encontrado                  │
│  /var/log/squid                             │
╰─────────────────────────────────────────────╯

┌────────────────────────┬────────────────────┐
│ Primer log             │ 2025-02-06         │
│ Último log             │ 2026-05-02         │
│ Cobertura              │ 451 días  (~1 año) │
└────────────────────────┴────────────────────┘

┌────────────────────────┬───────┐
│ Logs activos           │ 3     │
│ Logs rotados           │ 450   │
│   Comprimidos          │ 445   │
│   Sin comprimir        │ 5     │
│ Total archivos         │ 453   │
└────────────────────────┴───────┘

┌────────────────────────┬──────────┐
│ Tamaño total           │ 8.3 GB   │
│ Promedio diario        │ 18.9 MB  │
│ Rotados sin comprimir  │ 245.0 MB │
└────────────────────────┴──────────┘

  ✓ Retención anual detectada (451 días)
  ⚠  Rotación dual detectada — mezcla de rotación por número y por fecha
```

---

## Diagnósticos automáticos

| Diagnóstico                      | Cuándo se activa                                     |
|----------------------------------|------------------------------------------------------|
| ✓ Retención anual                | Cobertura ≥ 360 días                                 |
| ⚠ Retención corta                | Cobertura < 60 días                                  |
| ⚠ Rotación dual                  | Mezcla de `.1/.2` y `-YYYYMMDD.gz` en el mismo dir  |
| ⚠ Sin rotación detectada         | Solo archivos activos, sin ningún rotado             |
| ⚠ Logs sin comprimir acumulados  | Más de 5 rotados sin comprimir                       |
| ℹ Squid: access.log grande       | Log activo supera 500 MB                             |
| ℹ Nginx: multi-virtualhost       | Múltiples access.log detectados                      |

---

## Estructura del proyecto

```
logscope/
├── main.py              ← Punto de entrada, CLI interactivo
├── config.py            ← Configuración central
├── requirements.txt
├── core/
│   ├── scanner.py       ← Motor de escaneo de filesystem
│   ├── parser.py        ← Clase base ServiceAnalyzer
│   ├── formatter.py     ← Presentación visual (Rich)
│   └── utils.py         ← Utilidades compartidas
└── services/
    ├── squid.py
    ├── nginx.py
    ├── pihole.py
    ├── adguard.py
    └── custom.py
```

---

## Añadir un nuevo servicio

1. Crea `services/miservicio.py` heredando de `ServiceAnalyzer`:

```python
from core.parser import ServiceAnalyzer

class MiServicioAnalyzer(ServiceAnalyzer):
    name = "miservicio"
    label = "Mi Servicio"
    default_paths = ["/var/log/miservicio"]
    log_patterns = ["access.log", "error.log"]
```

2. Regístralo en `services/__init__.py`:

```python
from services.miservicio import MiServicioAnalyzer
SERVICE_MAP["miservicio"] = MiServicioAnalyzer
```

3. Añade la entrada en `config.py → SERVICES`.

---

## Roadmap

- [ ] `--export report.json` — exportar análisis
- [ ] `--all` — escanear todos los servicios de una vez  
- [ ] Comparativa de retención entre servicios
- [ ] Soporte journalctl para servicios sin logs en disco
- [ ] Apache HTTP Server, HAProxy, Postfix
