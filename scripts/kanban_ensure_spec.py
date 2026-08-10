#!/usr/bin/env python3
"""Ensure cards in the Spec lane have schema fields + Obsidian review stub.

When you drag a card into **## Spec**, run::

  python3 scripts/kanban_ensure_spec.py --vault /opt/second-brain/vault

For each card in Spec:
  - set stage: spec, spec_accepted: no (unless already yes)
  - default product: second-brain if missing
  - if no ``spec:`` path: create ``agent-tasks/specs/<slug>.md`` and link it
  - optional: create product-repo ``.agents/specs/<date>-<slug>.md`` if product root known

Does **not** run LLM /spec interview. Does **not** auto-release.
Cancel/accept remain human (see agent-tasks/kanban-protocol.md).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

try:
    from kanban_schema import (  # type: ignore[import-not-found]  # noqa: E402
        KanbanCard,
        parse_board,
        render_board,
    )
except ImportError:  # pragma: no cover — schema lives in second-brain product
    KanbanCard = Any  # type: ignore[misc,assignment]
    parse_board = None  # type: ignore[assignment]
    render_board = None  # type: ignore[assignment]

PREFERRED_LANES = ["Backlog", "Spec", "Doing", "Blocked", "Done", "Archive"]
SPEC_LANE = "Spec"
DEFAULT_PRODUCT = "second-brain"


def _load_product_roots() -> dict[str, Path]:
    roots: dict[str, Path] = {}
    cfg = Path(
        os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        or Path.home() / "agent-harness" / "config" / "night_shift_products.yaml"
    )
    if not cfg.is_file():
        cfg = ROOT.parent / "agent-harness" / "config" / "night_shift_products.yaml"
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            line = line.lstrip("-").strip()
            pid, proot = line.split(":", 1)
            p = Path(proot.strip().strip("\"'")).expanduser()
            if p.is_dir():
                roots[pid.strip()] = p
    # defaults
    home = Path.home()
    for pid, rel in (
        ("second-brain", home / "second-brain"),
        ("watchlist", home / "watchlist"),
        ("agent-harness", home / "agent-harness"),
        ("email-detach", home / "email-detach"),
        ("substack-push", home / "substack-push"),
        ("catalyxt", home / "catalyxt-website"),
        ("ocr-ledger", home / "ocr-ledger"),
    ):
        if pid not in roots and rel.is_dir():
            roots[pid] = rel
    return roots


def _slug(title: str, card_id: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = base[:48].strip("-") or "card"
    # drop T- prefix noise
    tid = card_id.replace("T-", "").lower()
    return f"{base}-{tid}"


def _write(path: Path, text: str) -> None:
    try:
        from vault_fs import write_text as _vault_write  # type: ignore
    except ImportError:
        _vault_write = None  # type: ignore
    if _vault_write is not None:
        _vault_write(path, text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except PermissionError:
        r = subprocess.run(
            ["sudo", "-u", "secondbrain", "tee", str(path)],
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            raise PermissionError(r.stderr.decode(errors="replace"))


def _stub_body(
    *,
    card_id: str,
    title: str,
    product: str,
    git_rel: str,
    vault_rel: str,
) -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""---
tags:
  - type/meta
  - domain/ops
  - topic/kanban
---
# {title}

**Kanban:** {card_id}
**Product:** {product}
**Canonical (git):** `{product}` repo → `{git_rel}`
**Obsidian:** `{vault_rel}`

## Goal

_(Fill after /spec interview or edit here.)_

## Acceptance Criteria

- [ ] …
- [ ] …

## Human decisions (ambiguities)

| # | Question | Default | Your answer |
|---|----------|---------|-------------|
| Q1 | | | |

- [ ] Decisions filled
- [ ] **Spec accepted** → set card `spec_accepted: yes`, then orchestrator `--step`
- [ ] **Cancelled** → move card to Done with notes cancelled; leave `spec_accepted: no`

## Created

Stub auto-created **{day}** by `kanban_ensure_spec.py` when card entered **Spec** lane.
Run full `/spec` to replace this stub with a real product-scoped spec, then re-sync this mirror if needed.
"""


def _git_spec_rel(product: str, slug: str) -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f".agents/specs/{day}-{slug}.md"


def ensure_card(
    card: KanbanCard,
    *,
    vault: Path,
    product_roots: dict[str, Path],
    dry_run: bool,
) -> dict:
    actions: list[str] = []
    product = (card.product or DEFAULT_PRODUCT).strip()
    if not card.product:
        card.product = product
        actions.append(f"set product={product}")
    # Never downgrade an in-flight ship stage back to spec
    if (card.stage or "").strip().lower() in {"", "backlog", "spec"}:
        card.stage = "spec"
    if not card.spec_accepted:
        # keep false; only note if we touch
        pass
    # do not reset accepted yes
    slug = _slug(card.title, card.id)
    vault_rel = f"agent-tasks/specs/{slug}.md"
    git_rel = _git_spec_rel(product, slug)

    if not card.spec or not str(card.spec).strip():
        card.spec = vault_rel
        actions.append(f"set spec={vault_rel}")
    else:
        vault_rel = card.spec.strip()
        if vault_rel.startswith("[["):
            # wikilink — still try agent-tasks path
            vault_rel = f"agent-tasks/specs/{slug}.md"

    # Confine stub writes to the vault root (reject absolute / path-traversal specs).
    vault_root = vault.resolve()
    safe_rel = vault_rel.strip().lstrip("/")
    if (
        not safe_rel
        or Path(vault_rel).is_absolute()
        or ".." in Path(safe_rel).parts
        or safe_rel.startswith("[[")
    ):
        safe_rel = f"agent-tasks/specs/{slug}.md"
        vault_rel = safe_rel
        card.spec = vault_rel
        actions.append(f"sanitized unsafe spec path → {vault_rel}")
    vault_path = (vault_root / safe_rel).resolve()
    try:
        vault_path.relative_to(vault_root)
    except ValueError:
        vault_rel = f"agent-tasks/specs/{slug}.md"
        safe_rel = vault_rel
        card.spec = vault_rel
        vault_path = (vault_root / safe_rel).resolve()
        actions.append(f"sanitized escaped spec path → {vault_rel}")

    created_vault = False
    if not vault_path.is_file():
        body = _stub_body(
            card_id=card.id,
            title=card.title,
            product=product,
            git_rel=git_rel,
            vault_rel=vault_rel,
        )
        if not dry_run:
            _write(vault_path, body)
        created_vault = True
        actions.append(f"create Obsidian stub {vault_rel}")

    # optional product git stub (only if missing)
    root = product_roots.get(product)
    created_git = False
    if root:
        git_path = root / git_rel
        if not git_path.is_file():
            body = (
                f"# {card.title}\n\n"
                f"- **Product:** {product}\n"
                f"- **Kanban:** {card.id}\n"
                f"- **Status:** draft (stub from Spec lane)\n"
                f"- **Obsidian:** `{vault_rel}`\n\n"
                f"## Problem Statement\n\n_\n\n## Acceptance Criteria\n\n- [ ] …\n\n"
                f"## Human decisions\n\n- [ ] Spec accepted\n- [ ] Cancelled\n"
            )
            if not dry_run:
                try:
                    git_path.parent.mkdir(parents=True, exist_ok=True)
                    git_path.write_text(body, encoding="utf-8")
                    created_git = True
                    actions.append(f"create git stub {product}:{git_rel}")
                except OSError as exc:
                    actions.append(f"git stub skip ({exc})")
    else:
        actions.append(f"no product root for {product} — Obsidian stub only")

    if not card.next_skill:
        # Match next_skill to current stage (do not force "spec" when the card
        # already advanced past Spec while still sitting in the Spec lane).
        st = (card.stage or "").strip().lower()
        if st in {"", "backlog"}:
            st = "spec"
        if st and st != "done":
            card.next_skill = st
            actions.append(f"set next_skill={st}")

    return {
        "card_id": card.id,
        "actions": actions,
        "created_vault_stub": created_vault,
        "created_git_stub": created_git,
        "spec": card.spec,
        "product": card.product,
        "dry_run": dry_run,
    }


def run_ensure(vault: Path, *, dry_run: bool = False) -> tuple[str, list[dict]]:
    from kanban_fs import board_lock  # noqa: WPS433

    board = vault / "agent-tasks" / "kanban.md"
    with board_lock(board):
        text = board.read_text(encoding="utf-8")
        preamble, lanes, other = parse_board(text)
        # ensure Spec lane exists
        lanes.setdefault(SPEC_LANE, [])
        for name in PREFERRED_LANES:
            lanes.setdefault(name, [])

        reports: list[dict] = []
        roots = _load_product_roots()
        new_spec_cards: list[KanbanCard] = []
        for card in lanes.get(SPEC_LANE, []):
            if card.done:
                new_spec_cards.append(card)
                continue
            rep = ensure_card(card, vault=vault, product_roots=roots, dry_run=dry_run)
            reports.append(rep)
            new_spec_cards.append(card)
        lanes[SPEC_LANE] = new_spec_cards

        order = [x for x in PREFERRED_LANES if x in lanes] + [
            x for x in lanes if x not in PREFERRED_LANES
        ]
        new_text = render_board(preamble, lanes, other, lane_order=order)
        if not dry_run and new_text != text:
            _write(board, new_text)
        return new_text, reports


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=None, help="Vault root (or PRODUCT_VAULT_ROOT)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.vault is None:
        import os
        env = (os.environ.get("PRODUCT_VAULT_ROOT") or "").strip()
        if not env:
            print("Set --vault or PRODUCT_VAULT_ROOT", file=sys.stderr)
            return 2
        args.vault = Path(env)
    vault = args.vault.expanduser().resolve()
    board = vault / "agent-tasks" / "kanban.md"
    if not board.is_file():
        print(f"❌ board not found: {board}", file=sys.stderr)
        return 1
    _, reports = run_ensure(vault, dry_run=args.dry_run)
    print(json.dumps({"reports": reports, "dry_run": args.dry_run}, indent=2))
    if not reports:
        print("No cards in Spec lane (drag a card into ## Spec then re-run).")
    elif args.dry_run:
        print("(dry-run — board/stubs not written)")
    else:
        print(f"✅ ensured {len(reports)} Spec card(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
