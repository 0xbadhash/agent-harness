"""Repo-rooted fixtures for the 50-enhancement spec tests (agent-harness copy).

Same determinism contract as the standalone suite: filesystem/AST/text checks
and offline imports only - no network, no LLM calls, no sleeps.
"""
from pathlib import Path

AH = Path(__file__).resolve().parents[2]   # agent-harness repo root
WH = Path("/home/debian/workflow-harness")  # sibling repo, absolute (E35 only)

def ah(*parts): return AH.joinpath(*parts)
def wh(*parts): return WH.joinpath(*parts)
def text_of(path):
    if not path.is_file():
        raise AssertionError(f"required artifact missing: {path}")
    return path.read_text(encoding="utf-8", errors="replace")
def src(path): return text_of(path)
def must_contain(path, *needles):
    body = text_of(path); missing = [n for n in needles if n not in body]
    if missing: raise AssertionError(f"{path} lacks required marker(s): {missing}")
def functions_of(path):
    import ast
    tree = ast.parse(text_of(path))
    return {n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def imports_of(path):
    import ast
    tree = ast.parse(text_of(path)); names=set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: names.add(node.module.split(".")[0])
    return names
