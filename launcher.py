"""One-click local browser launcher from the checked-out repository.

No pip install, Nitrado account, token, game client or internet required.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
import webbrowser


def _data_directory() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "DayZConsoleObservatory"
    return Path.home() / ".local" / "share" / "DayZConsoleObservatory"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Launch private DayZ Console Observatory in a browser")
    parser.add_argument("--check", action="store_true", help="Validate launcher without opening a port")
    parser.add_argument("--no-browser", action="store_true", help="Print the local URL without auto-opening it")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        print("DayZ Console Observatory requires Python 3.10 or newer.", file=sys.stderr)
        return 2
    project = Path(__file__).resolve().parent
    sys.path.insert(0, str(project / "src"))
    try:
        from dayz_observatory.server import make_server
    except ImportError:
        print("Source folder missing. Please extract the full repository, not only launcher.py.", file=sys.stderr)
        return 2
    if args.check:
        print("Launcher OK. Python and local source are available; no network used.")
        return 0
    folder = _data_directory()
    folder.mkdir(parents=True, exist_ok=True)
    db = folder / "observatory.sqlite"
    try:
        try:
            server = make_server(str(db), server="local", port=8765)
        except OSError:
            server = make_server(str(db), server="local", port=0)
    except OSError:
        print("Could not open the local service. Check local firewall/permissions.", file=sys.stderr)
        return 2
    url = f"http://127.0.0.1:{server.server_port}/"
    print("DayZ Console Observatory")
    print("Local-only workspace:", url)
    print("Data stored on this computer. To stop, close this window or press Ctrl+C.")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
