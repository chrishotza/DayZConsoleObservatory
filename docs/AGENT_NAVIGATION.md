# Navigation contract for automated agents

The source of truth for a compact machine-consumable overview is `project-index.json`; for prioritization and invariants, `AGENTS.md`. These files are deliberately small and link out only when necessary. Do not paste full guides into prompts before the task is known.

| Query | Read first | Time budget target |
| --- | --- | --- |
| "Where is the GUI?" | `web/index.html`, `web/app.js`, `server.py` | 3 files |
| "Why can't Kenneth use live ESP?" | `docs/PRODUCT_STRATEGY.md` | 1 file |
| "How to run?" | `docs/GUI_GUIDE.md` | 1 file |
| "How to contribute?" | `CONTRIBUTING.md`, selected test | 2 files |
| "Does Nitrado really work?" | `docs/NITRADO_VALIDATION.md`, `nitrado.py` | 2 files |

No AI tools or agents have been granted access to game accounts or external services by the repo. All tests until now are synthetic unless the owner later adds documented field evidence.
