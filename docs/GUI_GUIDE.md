# Open the browser app · GUI guide / Guía del panel

**Version 0.8.0, offline-tested prototype.** Does not modify DayZ, grant admin privileges, or use live ESP. No Nitrado account required for the browser demo.

## Windows · paso a paso

1. Download or clone the **entire** repository; extract ZIP before running it.
2. Install Python **3.10 or newer** if necessary. No `pip install` is required.
3. Double-click **`START_HERE.cmd`** in the extracted folder.
4. Your browser should open at `http://127.0.0.1:8765/`; if that port is in use, read the alternative address in the launcher window.
5. Click **Launch interactive demo** to explore clearly labeled synthetic examples.
6. Select **Choose .ADM file → Import file** to import a real local DayZ admin log. The UI switches to **My ADM records** and displays only that workspace.
7. Close the launcher terminal or press Ctrl+C to stop the local application.

On macOS/Linux, from the repository folder, use `python3 launcher.py`.

**Data directory:** Windows `%LOCALAPPDATA%\DayZConsoleObservatory`; macOS/Linux `~/.local/share/DayZConsoleObservatory`. The SQLite database is `observatory.sqlite`, and uploaded log copies stay under `private-imports/`. Store them securely. Data is persistent across restarts.

## Interactions

- **My ADM records / Demo:** two separate server namespaces within SQLite. Clicking Demo imports synthetic events into the demo namespace only. **Demo cannot pollute your actual records.**
- **Import:** accepts non-empty `.ADM` files up to 8 MiB, locally. Reimport the same file after it grows; byte-offset ingestion avoids duplicate records. Large logs may instead be imported with the advanced CLI.
- **Positions:** schematic X/Z coordinates from recorded snapshots, not a live map. Under the plot, expand **Read recorded positions as text** for a keyboard/screen-reader-friendly table of player names, X/Z coordinates and server-local observation times. The table is historical, not a live online-player list; it stays within the selected local/demo workspace.
- **Events:** pick a player or event kind to focus on observations.
- **Incident timeline:** choose a server-local range of at most 48 hours. Temporal adjacency is **not proof of player interaction**.
- **Auto refresh:** the interface refreshes local data; it does not poll Nitrado itself.

## Local security boundary

The HTTP service listens only at `127.0.0.1`. File upload POST requires same Origin, exact loopback Host, a custom header and a size limit; arbitrary paths/filenames cannot be chosen as upload destinations. No remote access or cloud upload exists in the GUI. It is **not an authenticated multiuser server**: never proxy, tunnel or open this port to the public internet. There is no automatic retention, encryption or synchronization of UI-uploaded files.

The **Nitrado connector** is an optional advanced command-line tool, not yet validated with a live Xbox service. The browser GUI does **not** ask for, display or store your token. Do not share ADM/RPT logs, personal player identifiers or private SQLite databases publicly.

## Diagnostics

- Browser does not open: copy the URL shown in the launcher window into your browser.
- Startup fails: check Python version and whether the full folder (including `src/`) was extracted.
- Import reports zero new events: the file may have been imported already, lack complete lines, or contain unsupported ADM grammar.
- No timestamps: DayZ ADM headers may be missing, have an impossible calendar day or invalid header time. The parser does not invent a date or assume UTC.
- Unknown events: the parser deliberately avoids guessing event types from substrings inside unrelated words. Extremely large coordinates that become non-finite are retained as unclassified text rather than placed on the map.
- For developer checks: `python launcher.py --check` and `python -m unittest discover -s tests -v`.

**Status:** CI tests Linux, Windows, and macOS offline (including Python 3.14). Automated platform smoke tests do not replace independent hardware validation or real DayZ/Nitrado service validation.
