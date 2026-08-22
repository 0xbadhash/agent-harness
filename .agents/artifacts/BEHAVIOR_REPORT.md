# BEHAVIOR-REPORT — night bar surface_inventory
**Marker:** BEHAVIOR-REPORT  
**Verdict:** PASS  

## Observed
- New inventory + watchlist-era check_hardcodes → EXIT 0.
- Old inventory FAIL on :33 artauthenticity; autofix rewrite → EXIT 0; merge still yields https://artauthenticity.xyz.
- Unit tests.test_surface_inventory green. No live --probe.
