# Offline end-to-end Nitrado self-test

No DayZ installation, Nitrado account, token or internet connection is needed. From your checkout, using Python 3.10 or newer:

    python -m pip install -e .
    dayz-observe selftest
    python -W error::ResourceWarning -m unittest discover -s tests -v

The command simulates the complete Nitrado workflow using the actual HTTP client code with a fake, strictly local transport. It exercises service metadata, ADM listing, a metadata-only probe, a dry run, signed downloads, caching, SQLite ingestion and an appended log received as an atomic file replacement.

The results contain no player names, server paths, credentials or identifying service information. They may be shared after review.

**A passing simulation does not verify real Nitrado Xbox compatibility.** That needs a consenting owner operating on their own private server and account using the optional read-only field probe. See [Community beta](COMMUNITY_BETA.md). Never share tokens, service IDs or raw ADM/RPT logs.