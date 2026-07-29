# Behavior contract — smoke_unit + vault group-write

- **Product:** agent-harness  
- **Target:** CLI smoke + vault ensure script  

## User tasks

1. Operator runs product smoke unit without bash -c in plugin.  
   - **Expect:** `python3 scripts/product_smoke.py` unit step exit 0; cmd contains smoke_unit.sh  
2. Operator can print resolved python: `bash scripts/smoke_unit.sh --print-python` exit 0.  
3. Operator runs vault check on temp or live vault; after --apply --sudo (if needed), check exit 0.  
4. Anti-cheat: plugin must not contain `bash", "-c"` unit smoke.  

## Must not
- Advance pipeline in these CLIs  
