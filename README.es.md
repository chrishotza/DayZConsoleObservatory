# DayZ Console Observatory

Herramienta **gratuita, abierta e independiente** para supervisar servidores comunitarios de **DayZ Microsoft Store PC / Xbox** sin modificar el cliente del juego.

> **Versión 0.5.0, experimental.** El parser, SQLite y el panel local han superado pruebas offline. El conector con Nitrado todavía no ha sido probado con un servidor real de un administrador. No automatiza sanciones.

## Funciones que ya incluye

- Importación de registros `.ADM` con posiciones, conexiones, desconexiones y algunos eventos.
- Conservación de registros desconocidos para ampliar el parser.
- Historial SQLite con detección de duplicados, líneas incompletas y rotaciones básicas.
- Gráfico X/Z local de las **últimas posiciones registradas**, no posiciones en vivo.
- Panel para revisar eventos administrativos y seleccionar un jugador para investigar su historial, posiciones y sesiones registradas.
- Comando `dayz-observe investigate ID_JUGADOR --db observatory.db` para exportar un historial JSON.
- Sincronización Nitrado de solo lectura para `dayzxb`: varios ADM recientes, caché SHA-256/metadatos, modo vista previa y reintentos HTTP limitados. El lector remoto de rangos `seek` aún no está implementado.

## Beta comunitaria: buscamos administradores voluntarios

Buscamos **3 a 5 dueños de servidores Xbox/Microsoft con Nitrado**. No necesitamos tokens, IDs ni registros privados. Podés probar sin DayZ con `dayz-observe beta-report --db observatory.db`; si sos dueño de un servidor, `dayz-observe nitrado TU_ID --probe` verifica metadatos **sin descargar logs** ni mostrar identificadores.

Seguí la [guía en español](docs/BETA_COMUNITARIA.es.md) y enviá tu [reporte a GitHub](https://github.com/chrishotza/DayZConsoleObservatory/issues/new/choose). La compatibilidad real con Nitrado todavía requiere validación independiente.


## Comunidad de GitHub: ayudanos sin tener DayZ

Ejecutá **dayz-observe selftest** para comprobar todo el flujo con un Nitrado simulado, sin cuenta ni juego instalado. Podés colaborar con pruebas en Windows, mejoras de accesibilidad, traducciones o registros ADM sintéticos. Consultá nuestra [guía de colaboración](docs/COMMUNITY_ROADMAP.md) y los [Issues](https://github.com/chrishotza/DayZConsoleObservatory/issues). **Esta simulación todavía no demuestra compatibilidad con Nitrado real.**


## Monitorización continua en primer plano (experimental)

Tras comprobar el servicio con `--probe`, podés ejecutar:

~~~powershell
$env:NITRADO_TOKEN = "<tu-token-local>"
dayz-observe nitrado TU_ID --watch --dry-run --cycles 2
dayz-observe nitrado TU_ID --watch --interval 300
~~~

El programa consulta como máximo una vez cada 300 segundos de forma predeterminada (mínimo 60), detiene las peticiones después de tres ciclos consecutivos con errores y solo muestra conteos anónimos. Se detiene con Ctrl+C. No obtiene coordenadas en vivo. La compatibilidad real con Nitrado sigue sin comprobarse. Ver [guía de operación](docs/WATCH_MODE.md).

## Comenzar con datos de demostración

Necesitás Python 3.10 o superior.

```bash
python -m pip install -e .
dayz-observe ingest samples/SYNTHETIC_dayz.ADM --db observatory.db
dayz-observe dashboard --db observatory.db
```

Abrí `http://127.0.0.1:8765` en tu navegador. Seleccioná un jugador en el panel de eventos para consultar su historial. Una sesión sin desconexión registrada **no demuestra** que el jugador esté conectado.

## Investigar tu servidor Nitrado (opcional)

El token debe configurarse en una variable de entorno de tu computadora. **Nunca lo publiques ni lo compartas.** En PowerShell:

```powershell
$env:NITRADO_TOKEN = "<tu-token>"
dayz-observe nitrado 12345678 --list-only
```

Reemplazá `12345678` por el ID de tu servicio. La primera operación solo lista archivos. Si se confirma que funciona en tu servicio:

```powershell
dayz-observe nitrado 12345678 --dry-run --out private-logs --db observatory.db
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
dayz-observe dashboard --db observatory.db --server 12345678
```

La segunda sincronización puede reutilizar los archivos locales si Nitrado informa tamaño y fecha válidos. Usá `--max-files 8` para ampliar el historial, `--force` para revalidar y `--include-rpt` solo si necesitás manejar datos sensibles. Consultá [docs/NITRADO_VALIDATION.md](docs/NITRADO_VALIDATION.md).

**Limitaciones importantes:** Los logs normalmente registran posiciones de jugadores cada cinco minutos. No equivalen a ESP en tiempo real, cámara libre, invisibilidad ni teletransporte. La versión Microsoft/Xbox no admite mods de Steam y este programa no intenta evadir el anticheat. Tampoco incluye imágenes oficiales de mapas que no tengamos permiso de reutilizar.

Podés colaborar con pruebas, mejoras del parser, traducciones y nuevas integraciones documentadas. Revisá [README.md](README.md) y [SECURITY.md](SECURITY.md) para detalles técnicos y privacidad.
