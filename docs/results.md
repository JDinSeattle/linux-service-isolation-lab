# Historical local baseline results

Preserved baseline; current maintenance results are in [refresh-results-20260907.md](refresh-results-20260907.md).

Execution date: 2026-09-07T21:44:24Z. 4 focused unit/regression tests passed, followed by the real integration campaign. See [validation log](../evidence/local/validation.log) and [manifest](../evidence/local/manifest.json).

CPU: 13th Gen Intel(R) Core(TM) i9-13900K. Kernel: 7.0.0-29-generic. All results are author-operated local measurements; cloud CI is a separate reproducibility check.

| Case | Observed enforcement |
|---|---|
| business_gemm | correct GEMM output; expected enforcement matched |
| read_allowed | syscall rc=0, errno=0; expected enforcement matched |
| write_allowed | syscall rc=0, errno=0; expected enforcement matched |
| read_outside | syscall rc=-1, errno=13; expected enforcement matched |
| write_outside | syscall rc=-1, errno=13; expected enforcement matched |
| symlink_escape | syscall rc=-1, errno=13; expected enforcement matched |
| network | syscall rc=-1, errno=1; expected enforcement matched |
| process_creation | syscall rc=-1, errno=1; expected enforcement matched |
| ptrace | syscall rc=-1, errno=1; expected enforcement matched |
| memory | syscall rc=-1, errno=12; expected enforcement matched |
| descriptors | syscall rc=-1, errno=24; expected enforcement matched |
| file_capacity | process return -25; expected enforcement matched |
| cpu_budget | process return -24; expected enforcement matched |
| wall_deadline | process return -9; expected enforcement matched |
| peer_auth_allowed | expected outcome matched; result True |
| peer_auth_wrong_operation | expected outcome matched; result False |
| peer_auth_uid_spoof | expected outcome matched; result False |

All 17 kernel/auth cases passed. Unconfined read/network/allocation controls succeeded before the sandbox rejected those operations. The file probe stopped at 32,768 bytes; CPU exhaustion received SIGXCPU; the parent killed and reaped a wall-timeout worker. [Full matrix](../evidence/local/matrix.json) contains errno, signals and durations. [Positive controls](../evidence/local/unconfined-controls.json) and [final assembly](../evidence/local/probe.disassembly.txt) support the enforcement claims.
