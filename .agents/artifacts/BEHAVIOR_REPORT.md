# BEHAVIOR-REPORT
**Marker:** BEHAVIOR-REPORT
**Runtime:** CI workflows + pr_validator skip path + zap script + property_tests check
## Scenarios
1. --skip-hard-gates without env → exit 1
2. property_tests enabled without coverage → hard_gates fail
3. daytime template requires hardcodes/secrets scripts
## Verdict
OK
