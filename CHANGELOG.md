# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-02

### Added
- Analizador interactivo de logs de sistema para Linux
- Soporte para múltiples servicios: Squid Proxy, Nginx, Pi-hole, AdGuard Home
- Detección automática de logs activos, rotados y comprimidos
- Diagnósticos automáticos sobre retención, rotación y uso de disco
- Interfaz interactiva con selector visual de servicios
- Configuración flexible mediante archivo services.json
- Asistente para añadir servicios personalizados
- Modo básico sin questionary para terminales sin soporte interactivo
- Salida formateada con Rich para mejor legibilidad
- Documentación completa con README mejorado

### Features
- Análisis de cobertura temporal de logs (primer y último log)
- Cálculo de tamaño total y promedio diario de logs
- Detección de rotación dual (por número y por fecha)
- Alertas de retención anual y retención corta
- Detección de logs sin comprimir acumulados
- Diagnósticos específicos por servicio (Squid, Nginx)
- Personalización de prefijos de búsqueda de logs
- Confirmación interactiva de rutas y prefijos

### Documentation
- README mejorado con secciones de uso, configuración y contribución
- Guía de solución de problemas
- Directrices para contribuir al proyecto
- Estructura del proyecto documentada

### Dependencies
- rich>=13.0.0 - Para formateo visual y tablas
- questionary>=2.0.0 - Para interfaz interactiva (opcional)

## [Unreleased]
