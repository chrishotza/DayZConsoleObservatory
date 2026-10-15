# DayZ Console Observatory — Proposal for an Official Admin Integration Pilot

**Status:** Community proposal; not submitted to or approved by Bohemia Interactive.  
**Date:** October 15, 2026  
**Project:** https://github.com/chrishotza/DayZConsoleObservatory  
**Target:** DayZ Microsoft Store PC / Xbox community servers, including Nitrado-hosted instances.

## Why this matters

Community operators need to intervene while incidents are happening, not only reconstruct events from logs afterward. Our current open-source project demonstrates a **read-only, local-first observability foundation** for ADM files. This is useful, but does **not** satisfy the most urgent administration requirements: trusted live player observation, spectator camera, teleportation, moderator invisibility, event actions and immediate rule enforcement.

This problem is not hypothetical. Bohemia's public feedback task [T197558 — Init.c Access to Console](https://feedback.bistudio.com/T197558) contains extensive community requests for safer console administration. On February 24, 2026, a Bohemia representative (Geez) stated that the team was exploring possible solutions while considering security. Multiple community participants reported that a short-lived, unofficial console admin panel had offered live administrative actions before the underlying access was closed. **Those descriptions are community reports, not a supported or authorized interface**.

The [official DayZ FAQ](https://dayz.com/faq) states that modding is not supported on console-related builds, including the Microsoft Store version. We respect that boundary.

## What we propose

A **permissioned, server-authoritative Console Admin API / approved partner pilot**, not a client injector, memory reader or anti-cheat bypass.

We request a technical discussion about any *existing or planned officially supported* route to implement these **server-owner-authorized administrative operations**:

| Capability | Administrative need | Proposed safety boundary |
| --- | --- | --- |
| Live observer / spectator view | Investigate reports without altering play | Read-only server-authorized spectator feed; admin-only; on authorized community servers |
| Teleport / unstuck | Support stranded players and run events | Explicit named role, target selection and recorded reason; audit trail and rate limits |
| Temporary moderation invisibility | Observe without interfering | Scoped admin spectator identity/state, not an undisclosed player-side cheat |
| Permissioned player markers | Detect griefing and investigate disputes | Admin-only marker stream with short retention and access logs |
| Immediate moderator actions | Respond to harmful behavior promptly | Authenticated, attributable, server-side checks; manual confirmation for sanctions |
| Safe zones / controlled events | Enable structured community play | Allowlisted actions, constrained duration/area and rollback |
| External observability | Preserve a documented evidence trail | Existing ADM/RPT and provider APIs, respecting platform quotas and privacy |

We **do not** request source access, unrestricted `init.c`, anti-cheat exceptions, client process injection or undocumented network access. A *small, allowlisted API or an approved integration interface* would be preferable to unrestricted script execution.

## Suggested security design

1. Opt-in for **private community servers only**. No support for third-party, official or unconsenting servers.
2. Server-authoritative identities and role-based access, with least privilege; no client may grant itself an admin role.
3. Short-lived credentials, revocation and explicit owner enrollment.
4. Action-specific authorization checks, quotas, audit logs and optional operator approval.
5. Transparent administrator activity policies for server communities, controlled retention and access to personal data.
6. No reverse engineering, binary modifications, anti-cheat avoidance or proprietary asset redistribution.
7. A dedicated, non-production test server and documented test cases before any privileged functionality.
8. Deployment only if permitted in writing by the relevant rights holders and platform/provider stakeholders.

## Existing open-source foundation

DayZ Console Observatory currently provides local ADM parsing, event persistence, historical coordinates and a local web interface. Its optional Nitrado connector is **experimental and read-only** and has **not been proven on a live Xbox server**. We are not claiming a working in-game admin system or a current commercial relationship with any publisher.

We can offer this source as a starting point for a proof-of-concept, adjust the design to official guidance, and recruit consenting community-server administrators for a pilot.

## Questions for Bohemia Interactive

1. Is there an approved path for a third-party **admin-only integration** for the DayZ Microsoft Store/Xbox server pool?
2. Does the team plan to expose a limited admin API, privileged service interface, or reviewed server-side scripting for community servers?
3. Could community developers participate in a developer preview, security-reviewed partner program, or technical consultation?
4. Which actions are technically supported or feasible by the server today (spectate/markers, teleport, invisibility, item spawning, safe zones, immediate sanctions), and which are deliberately unavailable?
5. Would permission or a separate license be required to distribute an open-source, noncommercial/admin-focused client for an official admin API? What review process would apply to commercial use?
6. Which parties should participate in review: Bohemia Interactive, Nitrado, Microsoft/Xbox and/or BattlEye?

We would welcome a short technical review call or written guidance; either an integration route **or a clear no-go specification** would help the community avoid unsafe approaches.

## Public evidence and policy references

- [Bohemia's community request T197558](https://feedback.bistudio.com/T197558), including an official response on February 24, 2026.
- [DayZ official FAQ](https://dayz.com/faq): console-related builds do not support modding.
- [Bohemia DayZ EULA](https://www.bohemia.net/en/licenses/dayz-end-user-license): source and binary modification, reverse engineering and cheats are restricted under the standard license.
- [Bohemia business and licensing contacts](https://www.bohemia.net/en/contacts).
- [Nitrado developer documentation](https://doc.nitrado.net/).

## Independence

Independent, unaffiliated community proposal. No endorsement, permission, partnership, sandbox or exception has been granted. Nothing in this document should be interpreted as authorization to bypass technical or contractual restrictions.
