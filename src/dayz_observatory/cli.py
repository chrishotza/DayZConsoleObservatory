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
from .sync import sync_once
from .beta import probe_nitrado, offline_beta_report
from .selftest import run_selftest, SelfTestError
from .watch import watch_foreground
from .casebook import build_case, save_case


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
    case = sub.add_parser("case", help="Save an aggregate-only player evidence summary by default")
    case.add_argument("player_id", help="Exact stable player ID (kept out of terminal output)")
    case.add_argument("--db", default="observatory.db")
    case.add_argument("--server", default="default")
    case.add_argument("--out", required=True, help="Destination JSON, must not already exist")
    case.add_argument("--limit", type=int, default=500)
    case.add_argument("--private", action="store_true", help="Explicitly include raw player IDs, names, coordinates and evidence lines")
    audit = sub.add_parser("audit", help="Inspect evidence quality without DayZ or Nitrado")
    audit.add_argument("--db", default="observatory.db")
    audit.add_argument("--server", default="default")
    beta = sub.add_parser("beta-report", help="Print privacy-safe aggregate counts from local data")
    beta.add_argument("--db", default="observatory.db")
    beta.add_argument("--server", default="default")
    sub.add_parser("selftest", help="Fully offline Nitrado integration check (no token, game or network)")
    n = sub.add_parser("nitrado", help="Inspect/download official Xbox service logs (read only)")
    n.add_argument("service_id", type=int)
    n.add_argument("--out", default="private-logs")
    n.add_argument("--db", default="observatory.db")
    n.add_argument("--server")
    mode = n.add_mutually_exclusive_group()
    mode.add_argument("--list-only", action="store_true", help="List available logs, do not download")
    mode.add_argument("--probe", action="store_true", help="Anonymized beta connectivity diagnostic")
    mode.add_argument("--watch", action="store_true", help="Bounded foreground log synchronization (no live ESP)")
    n.add_argument("--include-rpt", action="store_true", help="Download RPT too (contains sensitive identifiers)")
    n.add_argument("--max-files", type=int, default=3, help="Mirror up to N recent files (max 20)")
    n.add_argument("--dry-run", action="store_true", help="Preview only; write no local files")
    n.add_argument("--force", action="store_true", help="Ignore cached copy and download again")
    n.add_argument("--interval", type=int, default=300, help="Watch polling interval in seconds, minimum 60")
    n.add_argument("--cycles", type=int, help="Optional maximum watch cycles, for testing")
    args = p.parse_args(argv)
    if args.cmd == 'nitrado':
        if args.watch and args.force:
            p.error('--force cannot be combined with --watch')
        if args.cycles is not None and not args.watch:
            p.error('--cycles requires --watch')
    try:
        if args.cmd == "ingest":
            print(json.dumps(ingest(args.db,args.log,args.server),indent=2))
        elif args.cmd == "dashboard":
            serve(args.db,args.server,args.port)
        elif args.cmd == "investigate":
            print(json.dumps(player_history(args.db, args.server, args.player_id, args.limit), indent=2))
        elif args.cmd == "case":
            result = build_case(args.db, args.server, args.player_id,
                                private=args.private, limit=args.limit)
            save_case(args.out, result)
            print(json.dumps({"saved": True, "disclosure": result["disclosure"],
                              "events": result["event_count"],
                              "truncated": result["truncated"]}, sort_keys=True))
        elif args.cmd == "audit":
            print(json.dumps(get_quality_report(args.db, args.server), indent=2))
        elif args.cmd == "beta-report":
            print(json.dumps(offline_beta_report(args.db, args.server), indent=2))
        elif args.cmd == "selftest":
            print(json.dumps(run_selftest(), indent=2))
        elif args.cmd == "nitrado":
            api = NitradoClient()
            if args.watch:
                def emit_cycle(report):
                    print(json.dumps(report, sort_keys=True), flush=True)
                try:
                    result = watch_foreground(api, args.service_id, output=args.out, db=args.db,
                                              server=args.server, interval=args.interval,
                                              max_cycles=args.cycles, max_files=args.max_files,
                                              include_rpt=args.include_rpt, dry_run=args.dry_run,
                                              on_cycle=emit_cycle)
                except KeyboardInterrupt:
                    print(json.dumps({"status": "interrupted"}))
                    return
                print(json.dumps(result, sort_keys=True))
                if result["status"] == "stopped_after_errors":
                    raise SystemExit(2)
                return
            if args.probe:
                print(json.dumps(probe_nitrado(api, args.service_id), indent=2))
                return
            if args.list_only:
                directory, info = api.discover_log_directory(args.service_id)
                available = api.list_logs(args.service_id, directory)
                print(json.dumps({"game": info.get("game"), "files": [e.get("name") for e in available]}, indent=2))
                return
            report = sync_once(api, args.service_id, output=args.out, db=args.db,
                               server=args.server, max_files=args.max_files,
                               include_rpt=args.include_rpt, dry_run=args.dry_run, force=args.force)
            print(json.dumps(report, indent=2))
            if report["errors"]:
                raise SystemExit(2)
    except (OSError,NitradoError,SelfTestError,KeyError,ValueError) as exc:
        print(f"Error: {exc}",file=sys.stderr)
        raise SystemExit(1) from None

if __name__ == "__main__":
    main()
