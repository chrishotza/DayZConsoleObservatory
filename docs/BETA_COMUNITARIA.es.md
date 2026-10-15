# Beta comunitaria — DayZ Xbox / Microsoft Store

**Buscamos 3 a 5 administradores voluntarios** de servidores DayZ Xbox o Microsoft Store PC alojados en Nitrado. El proyecto es gratuito, experimental e independiente. **No** ofrece ESP dentro del juego, invisibilidad, teleportación ni cámara libre. No hace falta instalar DayZ para la primera prueba.

## Privacidad

**Nunca compartas tokens Nitrado, IDs de servicio/servidor, IPs, nombres o identificadores de jugadores, archivos ADM/RPT, bases SQLite ni capturas con información privada.** Usá un token de permisos mínimos, conservado en tu computadora, y revocá los temporales después de probar.

Solo pedimos resultados **agregados y anónimos** de nuestros comandos, revisados antes de publicarlos. No necesitamos acceso remoto a tu servidor.

## Prueba A: funciona sin servidor ni DayZ

Instalá Python 3.10 o superior y, desde la carpeta del repositorio:

```powershell
python -m pip install -e .
dayz-observe ingest samples/SYNTHETIC_dayz.ADM --db observatory.db
dayz-observe beta-report --db observatory.db
dayz-observe dashboard --db observatory.db
```

Abrí http://127.0.0.1:8765. Comprobá el panel y el historial de los jugadores ficticios. Ctrl+C para cerrarlo.

## Prueba B: verificar conexión a TU Nitrado, opcional

En Windows PowerShell, sustituí `TU_ID` por el número de tu servicio (NO lo compartas):

```powershell
$env:NITRADO_TOKEN = Read-Host 'Token de Nitrado'
dayz-observe nitrado TU_ID --probe
Remove-Item Env:NITRADO_TOKEN
```

El comando `--probe` **solo consulta metadatos**, detecta servicios Xbox y cuenta archivos ADM/RPT. No descarga logs ni extrae jugadores. El JSON de salida no incluye nombres, IDs, rutas o credenciales. Revisalo antes de compartirlo. Si falla, informá únicamente el tipo de error (401/403/404/429/timeout/incompatible).

## Prueba C: solo si querés continuar y sos propietario/autorizado

```powershell
dayz-observe nitrado TU_ID --dry-run --out private-logs --db observatory.db
dayz-observe nitrado TU_ID --out private-logs --db observatory.db
dayz-observe beta-report --db observatory.db --server TU_ID
```

No compartas los archivos descargados ni actives `--include-rpt`. El resumen `beta-report` contiene solo estadísticas anónimas.

## ¿Dónde aviso cómo salió?

Abrí [GitHub Issues](https://github.com/chrishotza/DayZConsoleObservatory/issues/new/choose), elegí **Community beta report** y contanos sistema operativo, Python, ronda probada, resultado y qué funciones administrativas necesitás. No adjuntes datos de jugadores.

**Todavía no tenemos pruebas independientes sobre un servidor real**. Necesitamos justamente esos reportes para dejar de depender de simulaciones.
