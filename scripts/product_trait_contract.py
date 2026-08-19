#!/usr/bin/env python3
"""Infer product traits (web / web3 / client_secrets) and required test categories.

Declare in ``product_plugin.yaml``::

  traits:
    web: auto          # true | false | auto (default)
    web3: auto
    client_secrets: auto

Inference (when auto / unset) does not invent a new skill:
  - web → existing ``detect_website`` / web_e2e contract
  - web3 → solana / web3 / ethers / viem / wallet / PDA / holder signals
  - client_secrets → bip39 / mnemonic / seed / secret-export signals

Required categories (fail closed via ``check_product_traits``):
  - web: Playwright + Comet (existing web_e2e_contract)
  - web3: ≥1 Comet+Playwright S-id whose id/title matches isolation
    (iso- / two-holder / IDOR / wrong-id-not-other-holder / …)
  - client_secrets: property_tests enabled on crypto modules + secret-wall S-id
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from product_plugin import load_plugin
from web_e2e_contract import (
    _SCENARIO_ID,
    _PLAYWRIGHT_TEST_TITLE,
    comet_doc_path,
    detect_website,
    find_e2e_specs,
)

# Isolation S-id / title signals (web3)
ISO_RE = re.compile(
    r"(?i)(\biso[-_]|isolation|two[-_]?holder|idor|"
    r"wrong[-_]?id|not[-_]?other[-_]?holder|cross[-_]?holder|"
    r"other[-_]?holder|holder[-_]?b\b)"
)

# Secret-wall S-id / title signals (client_secrets)
SECRET_WALL_RE = re.compile(
    r"(?i)(secret[-_]?wall|no[-_]?export|no[-_]?session[-_]?leak|"
    r"session[-_]?leak|mnemonic[-_]?leak|seed[-_]?leak|secret[-_]?export)"
)

WEB3_DEP_TOKENS = (
    "solana",
    "@solana",
    "web3",
    "ethers",
    "viem",
    "wagmi",
    "@wagmi",
    "walletconnect",
    "@walletconnect",
    "web3.js",
    "@web3",
)
WEB3_TEXT_RE = re.compile(
    r"(?i)\b(solana|web3|ethers|viem|wagmi|wallet|pda|holder|"
    r"metaplex|anchor\.|spl-token)\b"
)

CLIENT_SECRET_DEP_TOKENS = (
    "bip39",
    "@scure/bip39",
    "shamir-mnemonic",
    "mnemonic",
)
CLIENT_SECRET_TEXT_RE = re.compile(
    r"(?i)\b(bip39|mnemonic|seed\s*phrase|secret[-_]?export|"
    r"export[-_]?seed|recovery[-_]?phrase)\b"
)
# Path stems that mean *client* secrets (not harness check_secrets_diff / generic crypto)
CLIENT_SECRET_PATH_RE = re.compile(
    r"(?i)(bip39|mnemonic|shamir|seedphrase|seed_phrase|recovery)"
)
# Broader stems only used AFTER client_secrets is already active (property_tests coverage)
CRYPTO_MODULE_PATH_RE = re.compile(
    r"(?i)(bip39|mnemonic|seed|shamir|secret.?export)"
)


def _as_dict(x: Any) -> dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _trait_mode(raw: Any) -> str:
    """Normalize plugin trait value → true|false|auto."""
    if raw is True or str(raw).strip().lower() in ("true", "yes", "1", "on"):
        return "true"
    if raw is False or str(raw).strip().lower() in ("false", "no", "0", "off"):
        return "false"
    return "auto"


def _package_blob(root: Path) -> str:
    parts: list[str] = []
    for name in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod"):
        p = root / name
        if p.is_file():
            try:
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return "\n".join(parts)


def _dep_keys(root: Path) -> set[str]:
    keys: set[str] = set()
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        for block in ("dependencies", "devDependencies", "peerDependencies"):
            b = data.get(block)
            if isinstance(b, dict):
                keys.update(str(k).lower() for k in b)
    return keys


def infer_web3(root: Path, plugin: dict[str, Any] | None = None) -> tuple[bool, list[str]]:
    """Infer web3 from product deps / app paths — not harness docs under scripts/."""
    reasons: list[str] = []
    deps = _dep_keys(root)
    for tok in WEB3_DEP_TOKENS:
        if any(tok in k for k in deps):
            reasons.append(f"package.json dep~{tok}")
            break

    # Product-ish trees only (avoid scripts/docs that describe the gate itself)
    product_blob_parts: list[str] = []
    for base_name in ("src", "app", "web", "lib", "programs", "anchor"):
        base = root / base_name
        if not base.is_dir():
            continue
        for p in list(base.rglob("*"))[:120]:
            if not p.is_file():
                continue
            rel = str(p.relative_to(root)).replace("\\", "/")
            product_blob_parts.append(rel)
            if p.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".rs", ".py"} and p.stat().st_size < 200_000:
                try:
                    product_blob_parts.append(
                        p.read_text(encoding="utf-8", errors="replace")[:3000]
                    )
                except OSError:
                    pass
    product_blob = "\n".join(product_blob_parts)
    if product_blob and WEB3_TEXT_RE.search(product_blob):
        reasons.append("src/app/web/lib web3 signal")

    plugin = plugin if plugin is not None else load_plugin(root)
    stack = _as_dict(plugin.get("stack"))
    langs = " ".join(str(x) for x in (stack.get("languages") or [])).lower()
    hints = " ".join(str(x) for x in (plugin.get("domain_review_hints") or [])).lower()
    if any(t in langs or t in hints for t in ("solana", "web3", "wallet", "ethers", "viem")):
        reasons.append("plugin stack/hints web3")
    return bool(reasons), reasons


def infer_client_secrets(
    root: Path, plugin: dict[str, Any] | None = None
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    deps = _dep_keys(root)
    for tok in CLIENT_SECRET_DEP_TOKENS:
        if any(tok in k for k in deps):
            reasons.append(f"package.json dep~{tok}")
            break
    py = root / "pyproject.toml"
    if py.is_file():
        try:
            text = py.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            text = ""
        if any(t in text for t in ("bip39", "mnemonic", "shamir")):
            reasons.append("pyproject.toml secret/mnemonic")
    # Product-ish path stems only (not harness scripts/check_secrets_*.py)
    for base_name in ("src", "lib", "app", "web", "web/js"):
        base = root / base_name
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".mjs"}:
                continue
            if CLIENT_SECRET_PATH_RE.search(p.name) or CLIENT_SECRET_PATH_RE.search(
                str(p.relative_to(root))
            ):
                reasons.append(f"path:{p.relative_to(root)}")
                break
        if reasons and reasons[-1].startswith("path:"):
            break
    blob = _package_blob(root)
    if CLIENT_SECRET_TEXT_RE.search(blob):
        reasons.append("manifest client_secrets signal")
    plugin = plugin if plugin is not None else load_plugin(root)
    pid = str(plugin.get("product_id") or root.name).lower()
    if any(t in pid for t in ("bip39", "mnemonic", "seedphrase", "wallet-secret")):
        reasons.append(f"product_id={pid}")
    return bool(reasons), reasons


def discover_crypto_module_stems(root: Path) -> list[str]:
    """Heuristic module stems for property_tests when client_secrets is active."""
    stems: list[str] = []
    seen: set[str] = set()
    for base_name in ("src", "lib", "app", "web/js"):
        base = root / base_name
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".mjs"}:
                continue
            rel = str(p.relative_to(root)).replace("\\", "/")
            if not CRYPTO_MODULE_PATH_RE.search(p.stem) and not CRYPTO_MODULE_PATH_RE.search(
                rel
            ):
                continue
            if any(
                part in rel
                for part in ("node_modules/", "e2e/", "tests/", ".venv/", "dist/")
            ):
                continue
            stem = p.stem
            if stem not in seen:
                seen.add(stem)
                stems.append(stem)
            if len(stems) >= 12:
                return stems
    return stems


def infer_traits(root: Path, plugin: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return trait activation map.

    Shape::

      {
        "web": {"active": bool, "mode": "auto|true|false", "reasons": [...]},
        "web3": {...},
        "client_secrets": {...},
      }
    """
    root = root.resolve()
    plugin = plugin if plugin is not None else load_plugin(root)
    declared = _as_dict(plugin.get("traits"))

    det = detect_website(root, plugin)
    web_mode = _trait_mode(declared.get("web", "auto"))
    if web_mode == "true":
        web_active, web_reasons = True, ["traits.web=true"]
    elif web_mode == "false":
        web_active, web_reasons = False, ["traits.web=false"]
    else:
        web_active, web_reasons = bool(det["has_website"]), list(det.get("reasons") or [])

    w3_mode = _trait_mode(declared.get("web3", "auto"))
    if w3_mode == "true":
        w3_active, w3_reasons = True, ["traits.web3=true"]
    elif w3_mode == "false":
        w3_active, w3_reasons = False, ["traits.web3=false"]
    else:
        w3_active, w3_reasons = infer_web3(root, plugin)

    cs_mode = _trait_mode(declared.get("client_secrets", "auto"))
    if cs_mode == "true":
        cs_active, cs_reasons = True, ["traits.client_secrets=true"]
    elif cs_mode == "false":
        cs_active, cs_reasons = False, ["traits.client_secrets=false"]
    else:
        cs_active, cs_reasons = infer_client_secrets(root, plugin)

    return {
        "web": {"active": web_active, "mode": web_mode, "reasons": web_reasons},
        "web3": {"active": w3_active, "mode": w3_mode, "reasons": w3_reasons},
        "client_secrets": {
            "active": cs_active,
            "mode": cs_mode,
            "reasons": cs_reasons,
        },
    }


def _titles_from_specs(specs: list[Path]) -> list[str]:
    titles: list[str] = []
    for path in specs:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _PLAYWRIGHT_TEST_TITLE.finditer(text):
            titles.append(m.group(2).split("\n")[0].strip())
    return titles


def find_category_s_ids(
    *,
    pattern: re.Pattern[str],
    comet_text: str,
    specs: list[Path],
) -> tuple[set[str], set[str]]:
    """Return (playwright_s_ids, comet_s_ids) matching category pattern."""
    pw: set[str] = set()
    for title in _titles_from_specs(specs):
        if pattern.search(title):
            pw.update(_SCENARIO_ID.findall(title))
            # also allow local id without S-prefix in title if S-id present nearby — already have S
    comet: set[str] = set()
    for m in re.finditer(r"(S\d+[a-z]?)\b([^\n]{0,160})", comet_text or ""):
        window = m.group(0)
        if pattern.search(window):
            comet.add(m.group(1))
    # comet local ids in headings: ### S3 — iso-two-holder
    for m in re.finditer(
        r"(?im)^#+[ \t]*(S\d+[a-z]?)\b[^\n]*$", comet_text or ""
    ):
        line = m.group(0)
        if pattern.search(line):
            comet.add(m.group(1))
    return pw, comet


def isolation_s_ids(comet_text: str, specs: list[Path]) -> set[str]:
    pw, comet = find_category_s_ids(pattern=ISO_RE, comet_text=comet_text, specs=specs)
    return pw & comet if (pw and comet) else (pw & comet)


def secret_wall_s_ids(comet_text: str, specs: list[Path]) -> set[str]:
    pw, comet = find_category_s_ids(
        pattern=SECRET_WALL_RE, comet_text=comet_text, specs=specs
    )
    return pw & comet


def surfaces_have_isolation(surfaces: list[dict[str, Any]]) -> bool:
    for surf in surfaces:
        for sc in surf.get("scenarios") or []:
            if not isinstance(sc, dict):
                continue
            blob = f"{sc.get('id', '')} {sc.get('name', '')}"
            if ISO_RE.search(blob):
                return True
    return False


def surfaces_have_secret_wall(surfaces: list[dict[str, Any]]) -> bool:
    for surf in surfaces:
        for sc in surf.get("scenarios") or []:
            if not isinstance(sc, dict):
                continue
            blob = f"{sc.get('id', '')} {sc.get('name', '')}"
            if SECRET_WALL_RE.search(blob):
                return True
    return False


def ensure_trait_scenarios(
    surfaces: list[dict[str, Any]],
    traits: dict[str, Any],
) -> list[dict[str, Any]]:
    """Append named isolation / secret-wall scenarios when traits require them."""
    import copy

    out: list[dict[str, Any]] = copy.deepcopy(surfaces) if surfaces else []
    if not out:
        out = [
            {
                "id": "app",
                "order": 0,
                "path": "/",
                "title": "App",
                "playwright": "e2e/app.spec.ts",
                "scenarios": [],
            }
        ]
    target = out[0]
    target.setdefault("scenarios", [])
    assert isinstance(target["scenarios"], list)

    if traits.get("web3", {}).get("active") and not surfaces_have_isolation(out):
        target["scenarios"].append(
            {
                "id": "iso-two-holder",
                "name": (
                    "iso-two-holder — holder A never painted as holder B; "
                    "garbage id is plain English not another person"
                ),
                "steps": [
                    "Open / act as holder A",
                    "Open wrong-id / holder-B id in A session",
                    "Assert: UI never paints holder B as A",
                    "Assert: garbage id → plain English error (not another holder)",
                ],
            }
        )

    if traits.get("client_secrets", {}).get("active") and not surfaces_have_secret_wall(
        out
    ):
        target["scenarios"].append(
            {
                "id": "secret-wall-no-export",
                "name": (
                    "secret-wall — no export / no session leak of mnemonic or seed"
                ),
                "steps": [
                    "Load app with test vector only",
                    "Assert: no mnemonic/seed in export surfaces or sessionStorage",
                    "Assert: secret-wall copy never echoes full seed",
                ],
            }
        )
    return out


def evaluate_categories(root: Path) -> tuple[bool, list[str], dict[str, Any]]:
    """Fail-closed category check for inferred/declared traits.

    Returns (ok, messages, detail).
    """
    root = root.resolve()
    plugin = load_plugin(root)
    traits = infer_traits(root, plugin)
    msgs: list[str] = []
    detail: dict[str, Any] = {"traits": traits}

    cfg = _as_dict(plugin.get("web_e2e"))
    specs = find_e2e_specs(root, cfg) if traits["web"]["active"] or traits["web3"]["active"] or traits["client_secrets"]["active"] else []
    comet = comet_doc_path(root, cfg)
    comet_text = ""
    if comet.is_file():
        try:
            comet_text = comet.read_text(encoding="utf-8", errors="replace")
        except OSError:
            comet_text = ""

    # web — keep existing contract; do not re-implement (hard_gates already calls it)
    if traits["web"]["active"]:
        msgs.append(
            "ok: web trait active — categories enforced by web_e2e_contract "
            f"(reasons={traits['web']['reasons'][:3]})"
        )
    else:
        msgs.append("ok: web trait inactive")

    # web3 — isolation required
    if traits["web3"]["active"]:
        pw_iso, comet_iso = find_category_s_ids(
            pattern=ISO_RE, comet_text=comet_text, specs=specs
        )
        both = pw_iso & comet_iso
        detail["isolation_pw"] = sorted(pw_iso)
        detail["isolation_comet"] = sorted(comet_iso)
        detail["isolation_both"] = sorted(both)
        if not both:
            msgs.append(
                "fail: web3 trait requires ≥1 Comet+Playwright S-id whose id/title "
                "is isolation (iso- / two-holder / IDOR / wrong-id-not-other-holder); "
                "outcome: holder A never painted as holder B; garbage id plain English "
                f"(pw={sorted(pw_iso) or '∅'} comet={sorted(comet_iso) or '∅'}; "
                f"reasons={traits['web3']['reasons'][:4]})"
            )
        else:
            msgs.append(
                f"ok: web3 isolation S-id(s) in Comet+Playwright: {sorted(both)}"
            )
    else:
        msgs.append("ok: web3 trait inactive — isolation stubs not required")

    # client_secrets — property_tests + secret-wall S-id
    if traits["client_secrets"]["active"]:
        try:
            from check_property_tests import check as _prop  # type: ignore
            from check_property_tests import _load_modules  # type: ignore

            enabled, modules = _load_modules(root)
        except Exception as e:  # noqa: BLE001
            enabled, modules = False, []
            msgs.append(f"fail: client_secrets property_tests load error: {e}")

        crypto_stems = discover_crypto_module_stems(root)
        detail["crypto_stems"] = crypto_stems
        detail["property_tests"] = {"enabled": enabled, "modules": modules}

        if not enabled:
            msgs.append(
                "fail: client_secrets trait requires property_tests.enabled: true "
                "on crypto modules "
                f"(suggested stems: {crypto_stems or ['<declare bip39/mnemonic/seed module>']})"
            )
        elif not modules:
            msgs.append(
                "fail: client_secrets trait requires property_tests.modules "
                "listing crypto modules "
                f"(suggested: {crypto_stems or ['bip39', 'mnemonic']})"
            )
        else:
            # Prefer overlap with discovered stems; if none discovered, modules list is enough
            if crypto_stems:
                overlap = [
                    m
                    for m in modules
                    if any(s.lower() in m.lower() or m.lower() in s.lower() for s in crypto_stems)
                ]
                if not overlap:
                    msgs.append(
                        "fail: property_tests.modules must cover crypto stems "
                        f"{crypto_stems}; got {modules}"
                    )
                else:
                    prop_ok, prop_msgs = _prop(root)
                    if not prop_ok:
                        for pm in prop_msgs:
                            msgs.append(f"fail: property_tests — {pm}")
                    else:
                        msgs.append(
                            f"ok: property_tests cover crypto modules {overlap}"
                        )
            else:
                prop_ok, prop_msgs = _prop(root)
                if not prop_ok:
                    for pm in prop_msgs:
                        msgs.append(f"fail: property_tests — {pm}")
                else:
                    msgs.append(
                        f"ok: property_tests enabled with modules {modules}"
                    )

        # Need specs/comet for secret-wall even if web not otherwise detected
        if not specs:
            specs = find_e2e_specs(root, cfg)
        if not comet_text and comet.is_file():
            try:
                comet_text = comet.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
        pw_sw, comet_sw = find_category_s_ids(
            pattern=SECRET_WALL_RE, comet_text=comet_text, specs=specs
        )
        both_sw = pw_sw & comet_sw
        detail["secret_wall_both"] = sorted(both_sw)
        if not both_sw:
            msgs.append(
                "fail: client_secrets trait requires ≥1 Comet+Playwright S-id "
                "secret-wall (no export / no session leak) "
                f"(pw={sorted(pw_sw) or '∅'} comet={sorted(comet_sw) or '∅'})"
            )
        else:
            msgs.append(
                f"ok: client_secrets secret-wall S-id(s): {sorted(both_sw)}"
            )
    else:
        msgs.append("ok: client_secrets trait inactive")

    ok = not any(m.startswith("fail:") for m in msgs)
    return ok, msgs, detail
