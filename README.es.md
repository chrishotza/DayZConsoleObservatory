# DayZ Console Observatory

**Panel privado y gratuito para analizar registros de servidores comunitarios DayZ Xbox / Microsoft Store.** Código abierto bajo MIT, independiente de Bohemia, Nitrado y Microsoft.

[Guía visual](docs/GUI_GUIDE.md) · [Mapa para IA](AGENTS.md) · [Índice de documentación](docs/INDEX.md) · [English](README.md)

> **v0.8.0 — versión experimental.** El panel y las pruebas simuladas funcionan sin tener DayZ. **La conexión con un servidor Nitrado real todavía no fue validada.** No ofrece ESP en vivo, invisibilidad, cámara libre ni teleportación dentro del juego.

## Abrir el panel sin comandos

1. Instalá **Python 3.10 o superior**, descargá y descomprimí el repositorio completo.
2. En **Windows, hacé doble clic en `START_HERE.cmd`**. Se abrirá tu navegador en una dirección local. No hace falta instalar bibliotecas con pip.
3. Tocá **Launch interactive demo** para ver un ejemplo con jugadores ficticios, separado de los datos auténticos.
4. O seleccioná **Choose .ADM file → Import file** para cargar un registro de administrador desde tu PC, sin subirlo a internet.
5. Explorá posiciones históricas, eventos, jugadores e incidentes agrupados por horario.

En macOS/Linux podés abrirlo con `python3 launcher.py`. El panel solo escucha en `127.0.0.1`. Los archivos quedan en la carpeta de datos de usuario (`%LOCALAPPDATA%\DayZConsoleObservatory` en Windows). **No publiques ese puerto:** los registros reales pueden contener nombres, identificadores y coordenadas.

## Estado de funciones

| Disponible hoy | No disponible todavía |
| --- | --- |
| Aplicación web local y demo separada | Instalador .exe independiente de Python |
| Importación de ADM desde el navegador (hasta 8 MiB) | ESP en tiempo real y mapa de terreno oficial |
| Posiciones registradas, eventos e investigación histórica | Teleport, invisibilidad, espectador dentro del juego |
| Copias de SQLite, informes y controles de privacidad | Integración Nitrado real validada y permisos de Bohemia |

Las posiciones registradas pueden estar separadas por varios minutos. No indican dónde está alguien ahora ni prueban trampas por sí solas.

## Para administradores avanzados e IAs

El motor de Python mantiene comandos opcionales para análisis y diagnósticos. Para ejecutar la simulación integral sin internet:

```bash
python -m pip install -e .
dayz-observe selftest
python -W error::ResourceWarning -m unittest discover -s tests -v
```

Las pruebas son **simuladas y sin conexión**. La corrección de limpieza de respuestas HTTP 429/503 cierra los recursos antes de reintentar; si aparece un aviso `ResourceWarning` aun cuando el resultado sea `OK`, informalo en la [issue #5](https://github.com/chrishotza/DayZConsoleObservatory/issues/5) con tu versión de Python y un resumen sin datos privados.

Consultá [AGENTS.md](AGENTS.md), [project-index.json](project-index.json), [docs/INDEX.md](docs/INDEX.md) y [docs/NITRADO_VALIDATION.md](docs/NITRADO_VALIDATION.md).

No compartas tokens Nitrado, registros ADM/RPT reales, bases privadas ni identificadores de jugadores en GitHub. El navegador no solicita ni almacena contraseñas o tokens Nitrado.

La herramienta es independiente y no cuenta con aprobación o patrocinio oficial.
