# Behavior contract — root IoC home

- **Product:** agent-harness
- **Target:** CLI `python3 scripts/security_root_ioc_scan.py`
- **Setup:** no credentials. `HOME=/root` stands in for the systemd unit's process home. Do not walk `/home` or `/opt`.

## User tasks

1. As the operator, when the process home is `/root`, I can see the planned roots.  
   - **Expect:** stdout contains `required /home`, `root /home`, and `root /root`. Exit 0.  
   - **Anti-cheat:** stdout does not contain `status=ok`. A temp `PRODUCT_VAULT_ROOT` stays empty.

2. As the operator, I can pass `--home` and that path replaces `/root` and `/home`.  
   - **Expect:** `required <that path>`. Stdout does not contain `required /home`. Exit 0.

3. As the operator, I can read `--help` and see `--home`.  
   - **Expect:** help text contains `--home`.

## Must not

- Print `status=ok` from `--print-roots`.
- Write `security-ioc-status.md` during `--print-roots`.
- Walk the live host during this check.

## Evidence

- [x] CLI transcript (no secrets)
