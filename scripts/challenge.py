"""Two-model challenge: GLM and Deepseek, then a local decision on disk.

Round 1 sends only the proposal. Round 2 sends the proposal plus the other
model's critique. This script does not call a third model and does not edit
product source. The session agent supplies the decision text.

Exit 0: decision filed to the artifact and the vault.
Exit 2: both critiques are on disk; no decision was passed, vault untouched.
Exit 1: a model failed, or the vault write failed after both critiques.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

INSTRUCTION = (
    "Attack the proposal. Do not agree by default. Name what is wrong, "
    "what is weak, and what you would do instead. Do not invent files "
    "you were not given. Do not ask for secrets."
)
CROSS = (
    "Attack the other model's critique of the proposal. Say what it gets "
    "wrong, what it gets right, and whether the proposal should stand, "
    "change, or be rejected. Do not agree by default."
)


class ModelError(RuntimeError):
    pass


def _env_key(name: str) -> str:
    val = os.environ.get(name, "").strip()
    if val:
        return val
    for path in (str(Path.home() / "hermes" / ".env"), str(Path.home() / ".env")):
        try:
            for line in Path(path).read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    raise ModelError(f"{name} not found")


def call_glm(prompt: str) -> str:
    script = Path.home() / "hermes" / "scripts" / "ask_glm.py"
    if not script.is_file():
        raise ModelError("ask_glm.py missing")
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as fh:
        fh.write(prompt)
        name = fh.name
    try:
        proc = subprocess.run(
            [sys.executable, str(script), name, "--max-tokens", "2500"],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(name).unlink(missing_ok=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise ModelError("GLM failed")
    return proc.stdout.strip()


def call_deepseek(prompt: str) -> str:
    key = _env_key("DEEPSEEK_API_KEY")
    body = json.dumps({
        "model": os.environ.get("CHALLENGE_DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2500,
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        os.environ.get(
            "CHALLENGE_DEEPSEEK_URL",
            "https://" + "api.deepseek.com" + "/chat/completions",
        ),
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ModelError("Deepseek failed") from exc
    text = ((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    if not text.strip():
        raise ModelError("Deepseek empty")
    return text.strip()


def _slug(proposal_path: Path | None) -> str:
    if proposal_path is None:
        return "stdin"
    stem = proposal_path.stem.lower().replace(" ", "-")
    return "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in stem)[:60] or "proposal"


def _rounds(proposal: str, glm, deepseek) -> tuple[str, str, str, str]:
    g1 = glm(f"{INSTRUCTION}\n\n{proposal}")
    d1 = deepseek(f"{INSTRUCTION}\n\n{proposal}")
    g2 = glm(f"{CROSS}\n\nProposal:\n{proposal}\n\nOther critique:\n{d1}")
    d2 = deepseek(f"{CROSS}\n\nProposal:\n{proposal}\n\nOther critique:\n{g1}")
    return g1, d1, g2, d2


def _note(proposal: str, rounds: tuple[str, str, str, str], decision: str) -> str:
    """The artifact body. Every field is interpolated once, by an f-string: the proposal, the decision
    and both critiques are arbitrary user/model text, and feeding the assembled body through
    ``str.format`` made any brace in them a format field (``KeyError: 'a,b'`` on a proposal that
    happened to list ``{render_page,capture}.py``)."""
    g1, d1, g2, d2 = rounds
    return (
        "# Challenge\n\n"
        f"- **Date:** {datetime.now(UTC).strftime('%Y-%m-%d')}\n"
        "- **Models:** z-ai-glm-5-3-flash, deepseek-chat\n\n"
        "## Decision\n\n"
        f"{decision.strip()}\n\n"
        "## Proposal\n\n"
        f"{proposal.strip()}\n\n"
        "## GLM round 1\n\n"
        f"{g1.strip()}\n\n"
        "## Deepseek round 1\n\n"
        f"{d1.strip()}\n\n"
        "## GLM round 2\n\n"
        f"{g2.strip()}\n\n"
        "## Deepseek round 2\n\n"
        f"{d2.strip()}\n"
    )


def _vault_paths(product_root: Path, slug: str, vault: Path | None):
    from vault_resolve import project_rel, resolve_vault_root

    root = vault or resolve_vault_root(product_root=product_root, require_enabled=False)
    if root is None:
        root = Path(os.environ.get("PRODUCT_VAULT_ROOT", "/opt/second-brain/vault"))
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    note = root / project_rel(product_root, "challenges", f"{day}-{slug}.md")
    decisions = root / project_rel(product_root, "decisions.md")
    return note, decisions


def publish(note_body: str, product_root: Path, slug: str, vault: Path | None) -> None:
    note, decisions = _vault_paths(product_root, slug, vault)
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(note_body, encoding="utf-8")
    pointer = f"- {datetime.now(UTC).strftime('%Y-%m-%d')} — Challenge. See [[{note.with_suffix('').as_posix()}]].\n"
    if decisions.is_file():
        text = decisions.read_text(encoding="utf-8")
        if pointer not in text:
            decisions.write_text(text.rstrip() + "\n" + pointer, encoding="utf-8")
    else:
        decisions.write_text("# Decisions\n\n" + pointer, encoding="utf-8")


def main(argv: list[str] | None = None, *, glm=call_glm, deepseek=call_deepseek) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", default="-")
    ap.add_argument("--decision")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--vault", type=Path, default=None)
    args = ap.parse_args(argv)

    product = args.root.resolve()
    proposal_path = None if args.proposal == "-" else Path(args.proposal)
    proposal = sys.stdin.read() if proposal_path is None else proposal_path.read_text(encoding="utf-8")
    if not proposal.strip():
        print("empty proposal", file=sys.stderr)
        return 1
    slug = _slug(proposal_path)
    artifact = product / ".agents" / "artifacts" / "CHALLENGE.md"
    try:
        rounds = _rounds(proposal, glm, deepseek)
    except ModelError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not args.decision:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(_note(proposal, rounds, "(decision not written yet)"), encoding="utf-8")
        print(artifact)
        print("both critiques recorded; pass --decision to file the vault note", file=sys.stderr)
        return 2

    decision = Path(args.decision).read_text(encoding="utf-8")
    body = _note(proposal, rounds, decision)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(body, encoding="utf-8")
    print(body)
    try:
        publish(body, product, slug, args.vault)
    except OSError as exc:
        print(f"vault write failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
