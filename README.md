# logscope

Analizador interactivo de logs de sistema para Linux.

Detecta, clasifica y resume los logs de los servicios más comunes, con diagnósticos automáticos sobre retención, rotación y uso de disco.

---

## 📋 Características

- **Análisis automático**: Detecta logs activos, rotados y comprimidos
- **Diagnósticos inteligentes**: Alertas sobre retención, rotación y uso de disco
- **Interfaz interactiva**: Selector visual de servicios con confirmación de rutas
- **Soporte multi-servicio**: Squid, Nginx, Pi-hole, AdGuard Home y servicios personalizados
- **Configuración flexible**: Añade tus propios servicios fácilmente
- **Salida formateada**: Informes claros con Rich para mejor legibilidad

---

## 📦 Requisitos

- Python 3.7+
- Linux (diseñado para sistemas con `/var/log`)
- Permisos de root (sudo) para leer logs del sistema

### Dependencias

```bash
pip install -r requirements.txt
```

Las dependencias principales son:

- `rich>=13.0.0` - Para formateo visual y tablas
- `questionary>=2.0.0` - Para interfaz interactiva (opcional, sin él usa modo básico)

---

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/logscope
cd logscope

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🎯 Uso

### Ejecución básica

```bash
sudo python main.py
```

> **Nota**: Se recomienda `sudo` porque la mayoría de logs en `/var/log` requieren permisos de root.

### Flujo de uso

1. **Seleccionar servicio**: Elige entre los servicios predefinidos o añade uno personalizado
2. **Confirmar ruta**: Verifica o cambia la ruta de los logs detectada automáticamente
3. **Configurar prefijo**: Especifica el prefijo de archivos de logs (si aplica)
4. **Ver resultados**: Analiza la información de retención, rotación y uso de disco

### Modo sin questionary

Si no tienes `questionary` instalado, logscope funcionará en modo básico con selección por números.

---

## ⚙️ Configuración

### Archivo services.json

La configuración de servicios se almacena en `services.json`. Puedes editarlo manualmente o usar el asistente interactivo.

#### Estructura de un servicio

```json
{
  "id": "squid",
  "label": "Squid Proxy",
  "paths": ["/var/log/squid", "/var/log/squid3"],
  "log_prefix": "",
  "log_patterns": ["access.log", "cache.log"]
}
```

**Campos**:

- `id`: Identificador único del servicio (sin espacios)
- `label`: Nombre visible en el selector
- `paths`: Lista de rutas donde buscar logs
- `log_prefix`: Prefijo de archivos de logs (ej: "adguarddns" para "adguarddns\*.log")
- `log_patterns`: Patrones adicionales de archivos a buscar

### Añadir un servicio personalizado

#### Método 1: Asistente interactivo

1. Ejecuta `sudo python main.py`
2. Selecciona "➕ Agregar servicio"
3. Sigue las preguntas del asistente:
   - ID interno (ej: haproxy)
   - Nombre visible (ej: HAProxy)
   - Rutas de logs separadas por coma
   - Prefijo de archivos (opcional)
   - Patrones de archivo separados por coma (opcional)

#### Método 2: Edición manual

Edita `services.json` y añade tu servicio:

```json
{
  "id": "haproxy",
  "label": "HAProxy",
  "paths": ["/var/log/haproxy"],
  "log_prefix": "haproxy-",
  "log_patterns": ["access.log", "error.log"]
}
```

### Configuración de temas

Los colores de la interfaz se configuran en `config.py` bajo la variable `THEME`. Puedes personalizar los colores para:

- Títulos
- Mensajes de éxito, advertencia y error
- Información destacada y silenciada

---

## 📚 Servicios soportados

| Servicio     | Rutas por defecto                        |
| ------------ | ---------------------------------------- |
| Squid Proxy  | `/var/log/squid`, `/var/log/squid3`      |
| Nginx        | `/var/log/nginx`                         |
| Pi-hole      | `/var/log/pihole`, `/var/log/pihole.log` |
| AdGuard Home | `/opt/AdGuardHome/work`                  |
| Ruta custom  | La que tú indiques                       |

---

## 📊 Salida de ejemplo

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

## 🔍 Diagnósticos automáticos

| Diagnóstico                     | Cuándo se activa                                   |
| ------------------------------- | -------------------------------------------------- |
| ✓ Retención anual               | Cobertura ≥ 360 días                               |
| ⚠ Retención corta               | Cobertura < 60 días                                |
| ⚠ Rotación dual                 | Mezcla de `.1/.2` y `-YYYYMMDD.gz` en el mismo dir |
| ⚠ Sin rotación detectada        | Solo archivos activos, sin ningún rotado           |
| ⚠ Logs sin comprimir acumulados | Más de 5 rotados sin comprimir                     |
| ℹ Squid: access.log grande      | Log activo supera 500 MB                           |
| ℹ Nginx: multi-virtualhost      | Múltiples access.log detectados                    |

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

## 🗺️ Roadmap

- [ ] `--export report.json` — exportar análisis
- [ ] `--all` — escanear todos los servicios de una vez
- [ ] Comparativa de retención entre servicios
- [ ] Soporte journalctl para servicios sin logs en disco
- [ ] Apache HTTP Server, HAProxy, Postfix

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si quieres mejorar logscope, sigue estos pasos:

### Reportar problemas

Si encuentras un bug o tienes una sugerencia:

1. Abre un issue en GitHub describiendo el problema
2. Incluye información de tu sistema (distribución, versión de Python)
3. Proporciona pasos para reproducir el error (si es un bug)

### Proponer cambios

1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b mi-feature`)
3. Haz tus cambios siguiendo el estilo del código existente
4. Asegúrate de que el código funcione correctamente
5. Haz commit de tus cambios (`git commit -m 'Añadir mi feature'`)
6. Push a la rama (`git push origin mi-feature`)
7. Abre un Pull Request

### Añadir soporte para un nuevo servicio

Si quieres añadir soporte para un servicio no incluido:

1. **Añade el servicio a services.json** (ver sección de configuración)
2. **Prueba el servicio** ejecutando logscope y verificando que detecta los logs correctamente
3. **Documenta el cambio** actualizando este README con el nuevo servicio en la tabla de servicios soportados
4. **Envía un Pull Request** con tus cambios

### Directrices de código

- Sigue el estilo PEP 8 para Python
- Añade comentarios para código complejo
- Mantén las funciones pequeñas y enfocadas
- Prueba tus cambios antes de enviar un PR

---

## 🔧 Solución de problemas

### Problema: "No se detectó ninguna ruta automática"

**Causa**: El servicio no tiene logs en las rutas por defecto configuradas.

**Solución**:

- Usa la opción "Introducir otra ruta" para especificar la ruta correcta
- Verifica que los logs existen en el sistema
- Añade el servicio personalizado con la ruta correcta en `services.json`

### Problema: "Permission denied" al leer logs

**Causa**: No tienes permisos de root para leer los logs.

**Solución**:

- Ejecuta logscope con `sudo python main.py`
- O ajusta los permisos de los directorios de logs (no recomendado por seguridad)

### Problema: questionary no funciona correctamente

**Causa**: questionary no está instalado o hay problemas con la terminal.

**Solución**:

- Logscope automáticamente cambiará a modo básico sin questionary
- Para reinstalar: `pip install --upgrade questionary`
- Si persiste, usa el modo básico que es completamente funcional

### Problema: Diagnósticos incorrectos

**Causa**: Los patrones de rotación o prefijos no coinciden con tu configuración.

**Solución**:

- Usa la opción de personalizar el prefijo durante el análisis
- Edita `services.json` para ajustar los patrones de tu servicio
- Verifica que los nombres de archivos coinciden con los patrones configurados

### Problema: Logs comprimidos no se detectan

**Causa**: Los archivos comprimidos tienen un formato diferente al esperado (.gz, .bz2, etc.).

**Solución**:

- Actualiza el código en `core/scanner.py` para soportar el formato de compresión
- O descomprime los logs manualmente antes del análisis
