# Offline end-to-end Nitrado self-test

No DayZ installation, Nitrado account, token or internet connection is needed. From your checkout, using Python 3.10 or newer:

    python -m pip install -e .
    dayz-observe selftest
    python -W error::ResourceWarning -m unittest discover -s tests -v

The command simulates the complete Nitrado workflow using the actual HTTP client code with a fake, strictly local transport. It exercises service metadata, ADM listing, a metadata-only probe, a dry run, signed downloads, caching, SQLite ingestion and an appended log received as an atomic file replacement.

The results contain no player names, server paths, credentials or identifying service information. They may be shared after review.

**A passing simulation does not verify real Nitrado Xbox compatibility.** That needs a consenting owner operating on their own private server and account using the optional read-only field probe. See [Community beta](COMMUNITY_BETA.md). Never share tokens, service IDs or raw ADM/RPT logs.
## Windows / Python 3.14 regression verification (issue #5)

Windows can return `stat().st_dev` or `stat().st_ino` values outside SQLite's signed 64-bit `INTEGER` range. Current `store.py` normalizes these filesystem-only identifiers before ingestion, and `tests/test_windows_file_identity.py` reproduces the oversized-ID case without real server data. The CI matrix includes Windows Python 3.12 and 3.14; however, automated CI does not replace an independent Windows/macOS result.

On a **fresh checkout of the latest revision**, run the commands above and record your OS build, `python --version`, checkout commit (`git rev-parse --short HEAD` if Git is available), `dayz-observe selftest` pass/fail, and the full test count/pass/fail summary. For issue #5, report whether the SQLite `OverflowError` has disappeared under Python 3.14; if it persists, include a minimal synthetic-only traceback with file and line numbers. Review selftest JSON before posting it. Do **not** share player identities, raw logs, server/service IDs, access tokens, private filesystem paths, or local databases.
