# PR Draft — require /code_review after execute_dev

**Date:** 2026-07-25  
**Version:** 1.3.5  

## What Problem This Solves
code_review existed but agents skipped it after implement.

## Why This Change Was Made
Soft-auto (1): execute_dev must run /code_review unless review_scope prose-only.

## User Impact
Code ships get a mandatory closeout review step; docs-only still skippable.

## Evidence
Skill + ship-flow + catalog updates; reinstall across night_shift products.

## Things that look bad but are actually fine
1. Still agent-enforced not a binary hook — portable agents must follow skill.  
2. Same-session model may review own code unless CODE_REVIEW_MODEL set.  
3. cross_review still separate for large diffs.  
4. No phase advance from code_review.  
5. Products need reinstall to get skill copy.
