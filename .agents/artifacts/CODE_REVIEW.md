# CODE-REVIEW — night bar surface_inventory hardcodes (1.4.37)
**Marker:** CODE-REVIEW  
**Verdict:** PASS / approve  

## Findings
- No P0: hostname-only KNOWN table removes the external_url tripwire for stale scanners.
- known_url() preserves https at merge/probe time; pane still lists full URLs.
- Autofix is mechanical and bounded to CEO host tuple https→hostname + known_url wiring.
- Hardcodes proposal path no longer calls inventory a secret leak.
- Night-bar 73c2221 not included. Leftovers unstaged.

## Verdict
Approve v1.4.37.
