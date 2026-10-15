# GitHub community: contribute to DayZ Console Observatory

We welcome people who do not own DayZ. The project is open source, MIT licensed and independent of Bohemia, Xbox and Nitrado.

## First contributions

| Area | Suggested contribution | Validation |
| --- | --- | --- |
| Offline testing | Run the selftest on Windows, macOS or Linux | Sanitized outcome and Python version |
| Console/Nitrado compatibility | Try the metadata-only beta probe on a service you own | Anonymized success/failure; no access sharing |
| Parser | Invent a synthetic ADM example and add a test | Offline unit test |
| Reliability | Test rotated logs, network errors and missing metadata | Deterministic mocked API |
| User interface | Make the dashboard better on mobile and via keyboard | Screenshots with synthetic data |
| Docs | Improve setup, translations and examples | Reproducible instructions |
| Maps | Research legally reusable map imagery and accurate coordinates | Document license and calibration |
| Research | Explain what live admin functions server owners actually need | Clear user stories and source links |

## Start contributing

1. Read [CONTRIBUTING](../CONTRIBUTING.md) and [SECURITY](../SECURITY.md).
2. Run the instructions in [SELFTEST.md](SELFTEST.md).
3. Choose a GitHub issue marked [good first issue] or open a new feature request.
4. Submit a focused pull request with tests and synthetic fixtures.

Never publish server access tokens, player identifiers, device IDs, service IDs, confidential logs or proprietary game assets.

We also welcome 3–5 consenting DayZ Xbox/Microsoft Store Nitrado administrators for optional **read-only owner-controlled** validation: [Community beta](COMMUNITY_BETA.md).

## What this is not

It does not provide ESP inside DayZ, live teleport, freecam or invisibility. An independent [publisher-facing technical proposal](BOHEMIA_ADMIN_API_PROPOSAL.md) asks about a future, approved integration route. Do not imply that permission has been granted.