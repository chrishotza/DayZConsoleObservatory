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


### Standard Windows accounts without symlink privileges

Windows users without Developer Mode or administrator privileges may get **WinError 1314** from `Path.symlink_to()`. This restriction affects the **test fixture setup**, not the core read-only DayZ/Nitrado simulation.

For issue #5, the integration suite now has **two complementary tests**:

- `test_reject_symlink_destination_without_os_privileges` uses a simulated symlink classification to verify the synchronizer refuses the destination and never downloads to it, on every platform.
- `test_reject_symlink_destination` attempts a real OS symlink. It **skips only** if symlink creation is unsupported or denied by system permissions; on capable systems it verifies that the protected file is untouched.

A suite ending in `OK (skipped=N)` is a valid result when the skipped tests require unavailable OS features. There is **no need to run as administrator, enable Developer Mode, or change permissions to test the tool**. Please include the number of skips in a sanitized issue report. A failure other than permission-denied or unsupported-link creation is not silently skipped.

### Strict ResourceWarning checks (Windows and other platforms)

The read-only Nitrado adapter now closes HTTP error response streams before retrying (429/503) or surfacing an API/download error. The offline regressions exercise these paths with in-memory response bodies; no real network is used. For independent verification, run `python -W error::ResourceWarning -m unittest discover -s tests -p test_nitrado.py -v` as well as the full strict suite. If the interpreter prints an unraisable warning even with exit 0, report it separately with the Python version and sanitized traceback; exit 0 alone does not prove that finalizer warnings are absent.

**Strict-suite note:** The browser and HTTP tests also close expected local HTTP 4xx error bodies before checking status, avoiding unraisable warnings on strict Python 3.14. The CI exit code by itself is insufficient; check logs for `Implicitly cleaning up` as well.
