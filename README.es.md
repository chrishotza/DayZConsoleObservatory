# DayZ Console Observatory

Herramienta **gratuita, abierta e independiente** para supervisar servidores comunitarios de **DayZ Microsoft Store PC / Xbox** sin modificar el cliente del juego.

> **Versión 0.2, experimental.** El parser, SQLite y el panel local han superado pruebas offline. El conector con Nitrado todavía no ha sido probado con un servidor real de un administrador. No automatiza sanciones.

## Funciones que ya incluye

- Importación de registros `.ADM` con posiciones, conexiones, desconexiones y algunos eventos.
- Conservación de registros desconocidos para ampliar el parser.
- Historial SQLite con detección de duplicados, líneas incompletas y rotaciones básicas.
- Gráfico X/Z local de las **últimas posiciones registradas**, no posiciones en vivo.
- Panel para revisar eventos administrativos y seleccionar un jugador para investigar su historial, posiciones y sesiones registradas.
- Comando `dayz-observe investigate ID_JUGADOR --db observatory.db` para exportar un historial JSON.
- Conector Nitrado de solo lectura para investigar el acceso a registros en servicios `dayzxb`.

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
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
dayz-observe dashboard --db observatory.db --server 12345678
```

**Limitaciones importantes:** Los logs normalmente registran posiciones de jugadores cada cinco minutos. No equivalen a ESP en tiempo real, cámara libre, invisibilidad ni teletransporte. La versión Microsoft/Xbox no admite mods de Steam y este programa no intenta evadir el anticheat. Tampoco incluye imágenes oficiales de mapas que no tengamos permiso de reutilizar.

Podés colaborar con pruebas, mejoras del parser, traducciones y nuevas integraciones documentadas. Revisá [README.md](README.md) y [SECURITY.md](SECURITY.md) para detalles técnicos y privacidad.
