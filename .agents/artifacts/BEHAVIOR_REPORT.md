# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** .agents/artifacts/BEHAVIOR_CONTRACT.md
**Target:** `python3 scripts/security_root_ioc_scan.py` (CLI only, no host walk)

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Process home `/root` plans a required `/home` and does not claim clean | pass | `HOME=/root python3 scripts/security_root_ioc_scan.py --print-roots` exit 0. Stdout: `required /home`, `root /home`, `root /root`, `root /opt`. No `status=ok` line. `PRODUCT_VAULT_ROOT` temp dir stayed at 0 files. |
| 2 `--home` replaces the process home | pass | `HOME=/root ... --print-roots --home /tmp/ioc-home.nScv` exit 0. Stdout: `required /tmp/ioc-home.nScv` and `root /opt`. No `required /home`. |
| 3 `--help` documents `--home` | pass | Help lists `--home HOME` as the operator home that replaces `Path.home()`, and says `/home` is required when the process home is `/root`. |
| Deep plan still names containerd | pass | `--print-roots --deep` adds `root /var/lib/containerd`. |
| Live walk of `/home` or `/opt` | out_of_scope | This check must not scan the host. Pin detection stays on temp trees in the unit test. |

## Summary

- pass: 4 · fail: 0 · blocked: 0 · out_of_scope: 1
- NEXT_SKILL=/pr_review --validate
