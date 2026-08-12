# Sandbox policy (Tier C-4)

## Defaults on portfolio VPS

| Surface | Policy |
|---------|--------|
| Ship scripts | Run as product user; no root |
| Night shift | systemd user timers where possible |
| Root IoC scan | explicit `sudo` + weekly timer only |
| Secrets | never log; gitleaks/regex fail-closed |
| Network e2e | product-scoped URLs only |

## Agent host sandbox

Hosts may restrict tools (filesystem roots, network). Harness skills must not require unrestricted root or arbitrary outbound network beyond documented product APIs.

## Checklist

- [ ] Product install does not chmod 777
- [ ] No secrets in `.agents/artifacts/`
- [ ] Web e2e targets allowlisted hosts
