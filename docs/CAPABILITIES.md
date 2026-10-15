# Capability boundary and product fit

This project is a **DayZ Microsoft Store PC / Xbox service observability tool**, not a game client modification.

| Requested feature | Current implementation | What would be required |
| --- | --- | --- |
| ESP / see active players through walls | **Not provided.** Last positions in a standalone coordinate viewer only. | An authorized game-side live telemetry and rendering interface, currently not documented for Microsoft/Xbox DayZ. Do not label recorded ADM snapshots as live ESP. |
| Invisibility | **Not provided.** A moderator can review records without joining the server, but that is not character invisibility. | Explicit supported game-side admin state control; not identified for this platform. |
| Teleport active characters | **Not provided.** Changing future spawn configuration does not move a connected player. | An authorized game-side teleport command; not identified for this platform. |
| Free camera / spectator | **Not provided.** A web timeline/coordinate view is not the in-game free camera. | Official spectator/debug-camera feature accessible to console administrators; not identified. |
| Incident tracking and last recorded positions | **Offline-supported.** ADM parser, SQLite, local UI, player-specific incident timeline and reconstructed log sessions tested. | A real, authorized ADM log sample and deployment integration test. |
| Nitrado Xbox log access | **Experimental read-only adapter.** Mock-tested, not exercised against a real service. | A willing server owner to try list-only and download against their account. |
| Ban/whitelist/restart | Not implemented; deliberate safety boundary. | Verify service-specific endpoints/permissions, explicit owner approval, dry-run, auditable actions. |

## Research and verification standards

- Label every plotted point **recorded** or **unknown-date** and do not interpolate into invented actual paths.
- `adminLogPlayerList` samples are usually around five minutes apart; more frequent file polling is *not* higher player telemetry frequency.
- Keep Nitrado credentials outside the source tree. Do not request server credentials from volunteers; ask for **redacted** response shapes, timestamps and status codes instead.
- Treat reported device identifiers and IPs as private. This project does not perform automated bans or infer player cheating from speed between sparse samples.
- Do not add modifications of game client memory, anti-cheat bypasses, undocumented character-state writes, or proprietary map assets.

## The open product question

Before spending months developing the dashboard, talk to administrators about their actual needs:

1. Which platform does their **server** run on, and who hosts it?
2. Which administrative task hurts the most: investigations, player moderation, incident replay, suspicious base raids, performance, managing multiple servers, or **in-game ESP / TP / invisible spectator / freecam**?
3. Is an outside-the-game dashboard useful if the four in-game capabilities are unavailable?
4. Can they share an **anonymized** ADM sample and the result of a read-only Nitrado API discovery? Never ask them to share a token.

If the answer to (3) is no and (2) is exclusively in-game powers, **do not market this tool as solving their problem**. It serves a separate audience and can remain a useful community project.
