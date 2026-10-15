# Security and privacy

DayZ Console Observatory is an unofficial, read-only admin observability utility.

- Never place Nitrado tokens, game logs, device IDs or player identifiers in Git.
- The dashboard is bound to `127.0.0.1`. Do not expose its port publicly; it has no authentication layer.
- Nitrado credentials are read from `NITRADO_TOKEN` in the environment.
- The Nitrado adapter supports `GET` and downloads only; no ban, teleport or server write commands.
- Console logs may include identifiers and other player-related data. Inform staff, restrict access, and define a data retention policy.
- Movement outliers are **not proof** of cheating. Review manually using additional evidence.
- The program does not interact with the game client, inject code, read process memory, or interfere with anticheat.
- If a download URL points to an unexpected domain, the client refuses it; verify provider documentation before supporting additional hosts.
- Avoid automatic device-based bans. Device identifiers are not proof of an individual identity.

Report vulnerabilities privately to the repository owner. Do not open issues containing tokens or unredacted player logs.
