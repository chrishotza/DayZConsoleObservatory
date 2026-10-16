# Product strategy and evidence gates

**Internal engineering plan — no public outreach or claims of partner status.**

## Product goal

Solve actual console-community administration problems while being honest about which functions the DayZ platform exposes. Project leadership evaluates ideas by demonstrable operator value and evidence, not by adding features only to increase the version number.

## Workstream A: available external administration

- Nitrado metadata, ADM, log import, privacy-safe diagnostics: implemented with synthetic tests.
- Bounded foreground polling, rate control, event review and SQLite storage: implemented with synthetic tests; real-host integration requires consenting owner validation.
- Incidents and audit workflows: continue with privacy-preserving case exports and verified parser fixtures.
- No false promises of continuously sampled player locations, hardware ban APIs or live admin control.

## Workstream B: advanced in-game admin capabilities (proposal only)

| Operator need | Status as of 2026-10-15 | Evidence needed before implementing |
| --- | --- | --- |
| Admin-only ESP / live marker feed | No official console API identified | Documented Bohemia interface and player consent / role rules |
| Free camera / spectator mode | No official console API identified | Publisher-supported role and test server |
| Invisibility / ghost admin state | No official console API identified | Documented, server-authoritative action |
| Teleport / unstuck | No official console API identified | Documented operator permissions and audited transaction |
| Kick/ban/restart/config changes | Some supported via Nitrado settings and service interfaces | Verified permission scopes, dry-run, approval and rollback |

Propose a constrained, permissioned pilot through Bohemia rather than distributing client cheats or bypasses.

## Research desk and review responsibilities

- **Official sources desk:** Bohemia release notes, FAQ and feedback; update each assumption with source, access date and any contradiction.
- **Provider/API desk:** Nitrado REST/SDK contract, quotas, HTTP/redirect boundaries; distinguish code existence from successful console-hosted execution.
- **Open-source desk:** GitHub code inspection, licensing, dependencies, upstream security updates, reproducible fixtures.
- **Scientific methods desk:** trajectory reconstruction and measurement uncertainty; never label an inferred path as a measured track or auto-ban on sparse samples.
- **Quality desk:** CI on supported Python versions, local-only HTTP tests, privacy audit, synthetic end-to-end tests and gated field trials.

Suggested strengths: Claude for API correctness and security audits, Gemini for UI/UX and deployment flows, Grok for adversarial source checking; coordinate through source-backed issues and checked code, not assumed real-time conversations between models.

## Advancement gates

1. **Offline gate:** standard-library tests and a complete synthetic Nitrado transport pass.
2. **Owner gate:** read-only calls verified against an authorized Xbox Nitrado instance; only sanitized status shared.
3. **Moderation gate:** explicit roles, audit logs, owner confirmation and provider-permitted operations validated before any write API.
4. **In-game gate:** written Bohemia/platform permission and documented, controlled API before any spectator/teleport/admin game-state feature.

## Primary references

- https://community.bistudio.com/wiki/DayZ:Administration_Logs
- https://community.bistudio.com/wiki/DayZ:Server_Configuration
- https://feedback.bistudio.com/T197558 (official team noted a possible solution on Feb 24, 2026 without a release date)
- https://dayz.com/faq
- https://doc.nitrado.net/
- https://github.com/nitrado/NitrAPI-PHP

Last evidence review: 2026-10-15. Requests for official integration remain proposals, not approvals.
