# Interview preparation / 面试准备

Target: Linux security · platform engineering.

Explain the code path and one retained failure before citing any metric. All numbers must link to the checked-in evidence and its hardware/software manifest. A GitHub CI pass demonstrates reproducibility, not production use.

可陈述：独立实现、真实本地测试、故障定位、可复现证据。不可陈述：企业客户、生产规模、未测硬件成绩、上游已合并贡献、独立用户验收。先按 README 完整复现，再练习解释每个边界和失败。

## Evidence-led talking points

- Demonstrate kernel peer credentials and explain why a caller's JSON UID cannot authenticate itself. UID authorizes a local principal, not an identity shared across arbitrary machines.
- Explain the division of labor: Landlock restricts allowed filesystem objects; seccomp restricts syscall vocabulary; rlimits restrict individual process resources; the parent enforces wall time and reaps the process group.
- Show the positive control and actual errno/signal for a negative case. Failure without an unconfined control could merely indicate the host lacked the capability.
- Show the allocation probe before/after assembly. Test code can be optimized away; a test count alone says nothing about whether a resource boundary was exercised.
- Explain why per-file RLIMIT_FSIZE is not a total storage quota and address-space RLIMIT_AS is not RSS. Name cgroups/namespaces as future separate work, not existing functionality.

Resume wording, after reproducing: “Implemented a Linux CPU-worker broker using SO_PEERCRED authorization, executable digest pinning, Landlock and a seccomp allowlist; validated 17 kernel/auth scenarios, resource-limit signals, symlink restrictions and parent-enforced timeout cleanup with positive controls.” This does not constitute a production multi-tenant sandbox or independent security audit.
