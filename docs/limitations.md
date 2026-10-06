# Limitations and Residual Risk

1. Real-data M2 acceptance requires the exact accepted MeAJOR fingerprint and split contract in an environment containing the authoritative Parquet.
2. P1/P2/P3 are deterministic proxy/project labels, not human annotations.
3. URL intelligence is structural only; no live reputation, DNS, HTTP fetch or redirect following is enabled.
4. Attachments are metadata-only; no AV execution, sandboxing or detonation is performed.
5. HTML checks are heuristic structural indicators, not a complete browser security model.
6. Live provider OAuth requires external application configuration and consent.
7. The demo dashboard may hold an API key in session storage; production should use server-side identity/session handling.
8. SQLite is suitable for the prototype but not a horizontally scaled production persistence tier.
9. Distributed rate limiting, monitoring, managed secrets and rollback remain production responsibilities.
10. Model binaries are intentionally not committed; approved artifacts must be generated or supplied externally for a deployed instance.
