---
name: plan_backend
description: Structure a product roadmap from gap analysis (product fills domain content).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: PRODUCTION_GAP_ANALYSIS.md (or product equivalent), ENGINEERING_ASSURANCE.md
# Writes: product roadmap file (name from product_plugin.product_roadmap, often ROADMAP.md)
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/plan_backend`:
1. Pre-condition: gap analysis doc exists
2. Prioritize: P0 → P1 → P2
3. Each item: title, acceptance criteria, risk, dependencies
4. Write the product roadmap (not harness backlog)
5. Output: `✅ ROADMAP READY. Run /execute_dev`
