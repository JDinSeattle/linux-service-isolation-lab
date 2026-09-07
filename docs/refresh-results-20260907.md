# Maintenance validation — 2026-09-07

**8 focused tests passed**, followed by the real integration campaign. [Raw log](../evidence/refresh-20260907/validation.log) · [manifest](../evidence/refresh-20260907/manifest.json).

Run: 2026-09-07T22:43:15Z; Python 3.14.4, 13th Gen Intel(R) Core(TM) i9-13900K, Linux 7.0.0-29-generic. Single author-operated Linux CPU host. Hosted CI execution is separate.

All **17** real kernel/authorization cases and **3** unconfined positive controls matched expected behavior. The new 4 RPC regressions use actual Unix sockets: malformed/truncated/oversized input, a slow sender against a 150 ms total parsing budget, disconnect followed by a new policy-checked request, and replacement-path-safe cleanup.

The 150 ms budget is configured, not a measured latency percentile. The slow-peer test allows 600 ms wall time for scheduling and cleanup. File cap, CPU signal, syscall filtering, Landlock and wall-timeout results remain separately recorded.

[Kernel matrix](../evidence/refresh-20260907/matrix.json) · [positive controls](../evidence/refresh-20260907/unconfined-controls.json). No container/namespace or root-adversary boundary is claimed.
