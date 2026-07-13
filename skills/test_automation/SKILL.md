---
name: test_automation
description: Execute, scaffold, and validate multi-level test suites.
disable-model-invocation: true
user-invocable: true
max-retries: 1
timeout-seconds: 600
---
# Reads: tests/, config/coverage_config.json
# Writes: test files, coverage reports
# Anti-patterns: docs/AGENT_REFERENCE.md
When invoked with `/test_automation`:
1. Run full test suite
2. Check per-module coverage thresholds
3. Scaffold missing tests for uncovered paths
4. Validate test quality (no generic mocks at root)
5. Output coverage report
