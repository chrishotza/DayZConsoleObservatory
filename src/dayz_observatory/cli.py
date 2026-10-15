"""dayz-observe entrypoint; local-first CLI."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .store import ingest, get_quality_report
from .server import serve
from .nitrado import NitradoClient, NitradoError
from .investigate import player_history


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="dayz-observe", description="Open-source DayZ Xbox/Microsoft admin observability")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ingest", help="Import ADM locally (read only)")
    a.add_argument("log", type=Path)
    a.add_argument("--db", default="observatory.db")
    a.add_argument("--server", default="default")
    w = sub.add_parser("dashboard", help="Local-only web viewer")
    w.add_argument("--db", default="observatory.db")
    w.add_argument("--server", default="default")
    w.add_argument("--port", type=int, default=8765)
    q = sub.add_parser("investigate", help="Review recorded player timeline and log sessions (read only)")
    q.add_argument("player_id", help="Full stable identifier from ADM logs")
    q.add_argument("--db", default="observatory.db")
    q.add_argument("--server", default="default")
    q.add_argument("--limit", type=int, default=300)
    audit = sub.add_parser("audit", help="Inspect evidence quality without DayZ or Nitrado")
    audit.add_argument("--db", default="observatory.db")
    audit.add_argument("--server", default="default")
    n = sub.add_parser("nitrado", help="Inspect/download official Xbox service logs (read only)")
    n.add_argument("service_id", type=int)
    n.add_argument("--out", default="private-logs")
    n.add_argument("--db", default="observatory.db")
    n.add_argument("--server")
    n.add_argument("--list-only", action="store_true", help="List available logs, do not download")
    n.add_argument("--include-rpt", action="store_true", help="Download RPT too (contains sensitive identifiers)")
    args = p.parse_args(argv)
    try:
        if args.cmd == "ingest":
            print(json.dumps(ingest(args.db,args.log,args.server),indent=2))
        elif args.cmd == "dashboard":
            serve(args.db,args.server,args.port)
        elif args.cmd == "investigate":
            print(json.dumps(player_history(args.db, args.server, args.player_id, args.limit), indent=2))
        elif args.cmd == "audit":
            print(json.dumps(get_quality_report(args.db, args.server), indent=2))
        elif args.cmd == "nitrado":
            api = NitradoClient()
            directory, info = api.discover_log_directory(args.service_id)
            files = api.list_logs(args.service_id,directory)
            if args.list_only:
                print(json.dumps({"game":info.get("game"),"files":[e.get("name") for e in files]},indent=2))
                return
            target = Path(args.out).resolve()
            target.mkdir(parents=True,exist_ok=True)
            server = args.server or str(args.service_id)
            adm_files = [f for f in files if str(f.get("name","")).lower().endswith(".adm")]
            rpt_files = [f for f in files if str(f.get("name","")).lower().endswith(".rpt")]
            selected = sorted(adm_files,key=lambda e:str(e.get("modified_at", "")),reverse=True)[:1]
            if args.include_rpt:
                selected += sorted(rpt_files,key=lambda e:str(e.get("modified_at", "")),reverse=True)[:1]
            for e in selected:
                name = Path(str(e["name"])).name
                remote = str(e["path"])
                local = api.download_log(args.service_id,remote,target/name,directory)
                print(f"Downloaded {name}")
                if name.lower().endswith(".adm"):
                    print(json.dumps(ingest(args.db,local,server),indent=2))
    except (OSError,NitradoError,KeyError,ValueError) as exc:
        print(f"Error: {exc}",file=sys.stderr)
        raise SystemExit(1) from None

if __name__ == "__main__":
    main()
