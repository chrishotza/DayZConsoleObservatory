# Contributing

Thanks for helping improve DayZ Console Observatory. A DayZ copy or Nitrado account is **not** required for most code contributions.

**Quick entry:** [AI/dev map](AGENTS.md) · [Docs index](docs/INDEX.md) · [Browser GUI guide](docs/GUI_GUIDE.md).

1. Pick one area from `project-index.json`, then read only its corresponding source and test.
2. Reproduce bugs with **synthetic** ADM fixtures (never post real players' IDs or positions).
3. Run `python -m unittest discover -s tests -v` and `python launcher.py --check`.
4. Use a focused PR with the problem, reproduction, fix, added regression, and any documentation impact.
5. Respect security invariants in [SECURITY.md](SECURITY.md) and [AGENTS.md](AGENTS.md). Do not add unauthorized client game-state manipulation, anticheat circumvention or proprietary map files.
6. Never claim that a simulated Nitrado response proves real Xbox service compatibility.

The maintainer has **not authorized public outreach** yet. Issues/PRs may be prepared without sending promotional messages.
