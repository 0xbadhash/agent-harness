#!/usr/bin/env python3
"""Single Obsidian ops dashboard — what went well, failing, TODOs with links.

Writes (default):
  $PRODUCT_VAULT_ROOT/agent-tasks/OPS-DASHBOARD.md

Aggregates:
  - harness morning triage / night summary
  - catalyxt news day status
  - vault health / hygiene / pipeline status (if present)
  - security npm recheck (seed malware versions + payload IoCs)
  - kanban open counts (Backlog/Doing/Blocked)
  - portfolio harness lag

  python3 scripts/ops_dashboard.py
  python3 scripts/ops_dashboard.py --vault /opt/second-brain/vault --write
  python3 scripts/ops_dashboard.py --quick   # skip deep filesystem malware walk

Schedule (suggested):
  # after night shift / morning triage, and mid-day:
  0 1,12 * * * cd $HOME/agent-harness && python3 scripts/ops_dashboard.py --write
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HARNESS = Path(__file__).resolve().parents[1]
HKT = ZoneInfo("Asia/Hong_Kong")

MAL_SEED = {
    "keyv": "6.0.0",
    "flat-cache": "6.1.24",
    "file-entry-cache": "11.1.6",
    "cacheable": "2.5.1",
    "cacheable-request": "13.0.20",
    "cache-manager": "7.2.10",
    "ecto": "5.0.1",
    "@cacheable/net": "2.1.1",
    "@cacheable/node-cache": "3.1.2",
    "@cacheable/memory": "2.2.1",
    "@cacheable/utils": "2.5.1",
}


@dataclass
class Item:
    severity: str  # green | attention | fail | info
    area: str
    summary: str
    link: str = ""
    action: str = ""


@dataclass
class Dashboard:
    when_utc: str
    when_hkt: str
    overall: str  # GREEN | ATTENTION | RED
    went_well: list[Item] = field(default_factory=list)
    attention: list[Item] = field(default_factory=list)
    failing: list[Item] = field(default_factory=list)
    todos: list[Item] = field(default_factory=list)


def _vault_root(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit.expanduser().resolve()
    for env in ("PRODUCT_VAULT_ROOT", "WATCHLIST_VAULT_ROOT"):
        v = os.environ.get(env)
        if v and Path(v).is_dir():
            return Path(v).resolve()
    for cand in (
        Path("/opt/second-brain/vault"),
        Path.home() / "second-brain" / "vault",
    ):
        if cand.is_dir():
            return cand.resolve()
    return None


def _read(path: Path, limit: int = 200_000) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _wiki_link(vault: Path, rel: str, label: str | None = None) -> str:
    """Obsidian wikilink from agent-tasks/OPS-DASHBOARD.md to another vault note."""
    # Prefer path without .md for Obsidian
    p = rel[:-3] if rel.endswith(".md") else rel
    lab = label or Path(p).name
    return f"[[{p}|{lab}]]"


def collect_night(vault: Path | None, harness: Path) -> tuple[list[Item], list[Item], list[Item]]:
    well, att, fail = [], [], []
    summary = (vault / "01-Projects/harness-night-shift/SUMMARY.md") if vault else None
    triage = harness / ".agents/artifacts/MORNING_TRIAGE.md"
    text = _read(summary) if summary else ""
    if not text:
        text = _read(triage)
    if not text:
        att.append(
            Item(
                "attention",
                "night_shift",
                "No night-shift SUMMARY or MORNING_TRIAGE found",
                action="Run night_shift or morning_triage",
            )
        )
        return well, att, fail

    # Parse FAIL/PASS from summary table
    for line in text.splitlines():
        if "|" not in line or "Project" in line or "---" in line:
            continue
        if "FAIL" in line or "❌" in line:
            m = re.search(r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|", line)
            pid = m.group(1) if m else line.strip()[:40]
            link = ""
            if vault:
                link = _wiki_link(
                    vault,
                    f"01-Projects/{pid}/TODO.md",
                    f"{pid} TODO",
                )
            fail.append(
                Item(
                    "fail",
                    "night_shift",
                    f"Night readiness FAIL: **{pid}**",
                    link=link,
                    action=f"Open product TODO / re-run readiness for {pid}",
                )
            )
        elif "PASS" in line or "✅" in line:
            m = re.search(r"\|\s*`?([a-zA-Z0-9_-]+)`?\s*\|", line)
            if m and m.group(1) not in ("Project", "product"):
                well.append(
                    Item("green", "night_shift", f"Night readiness PASS: **{m.group(1)}**")
                )

    # triage product lines
    ttext = _read(triage)
    for line in ttext.splitlines():
        if "**FAIL**" in line or "| **FAIL**" in line:
            m = re.search(r"`([a-zA-Z0-9_-]+)`", line)
            if m:
                pid = m.group(1)
                if not any(pid in x.summary for x in fail):
                    link = ""
                    if vault:
                        link = _wiki_link(vault, f"01-Projects/{pid}/TODO.md", f"{pid} TODO")
                    fail.append(
                        Item(
                            "fail",
                            "night_shift",
                            f"Morning triage FAIL: **{pid}**",
                            link=link,
                            action="night_fail_remediate or fix product gates",
                        )
                    )

    if vault and summary and summary.is_file():
        for it in fail[:1]:
            it.link = it.link or _wiki_link(
                vault, "01-Projects/harness-night-shift/SUMMARY.md", "night SUMMARY"
            )
    return well, att, fail


def collect_news(vault: Path | None) -> tuple[list[Item], list[Item], list[Item], list[Item]]:
    well, att, fail, todos = [], [], [], []
    cat = Path.home() / "catalyxt.ltd"
    script = cat / "scripts" / "news_day_status.py"
    state = "unknown"
    detail = ""
    day = datetime.now(HKT).strftime("%Y-%m-%d")
    if script.is_file():
        r = subprocess.run(
            [sys.executable, str(script), "--date", day, "--no-write"],
            cwd=str(cat),
            capture_output=True,
            text=True,
            check=False,
        )
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"state=(\S+)", out)
        if m:
            state = m.group(1)
        for line in out.splitlines():
            if line.strip().startswith("Open") or "missing" in line.lower() or "Tick" in line:
                detail = line.strip()
                break
    status_md = cat / "content" / "news" / "STATUS.md"
    link = ""
    if vault:
        # news-inbox day
        inbox = f"01-Projects/catalyxt/news-inbox/{day}"
        if (vault / f"{inbox}.md").is_file():
            link = _wiki_link(vault, f"{inbox}.md", f"news inbox {day}")
        else:
            link = _wiki_link(vault, "01-Projects/catalyxt/TODO.md", "catalyxt TODO")

    if state == "published":
        well.append(Item("green", "news", f"Catalyxt news **published** for HKT {day}", link=link))
    elif state == "ready_to_publish":
        att.append(
            Item(
                "attention",
                "news",
                f"News ready to publish (ticks done) — HKT {day}",
                link=link,
                action="Wait publish timer or: publish_ready_news_inbox.py --deploy",
            )
        )
        todos.append(
            Item(
                "attention",
                "news",
                f"Publish news for {day}",
                link=link,
                action="python3 ~/catalyxt.ltd/scripts/publish_ready_news_inbox.py --deploy",
            )
        )
    elif state == "ready_to_tick":
        att.append(
            Item(
                "attention",
                "news",
                f"News candidates ready — **tick 3–5** in Obsidian (HKT {day})",
                link=link,
                action="Open news-inbox and tick 3–5 boxes",
            )
        )
        todos.append(
            Item(
                "attention",
                "news",
                f"Tick news inbox for {day}",
                link=link,
                action="Obsidian: 01-Projects/catalyxt/news-inbox/" + day,
            )
        )
    elif state == "missing_candidates":
        fail.append(
            Item(
                "fail",
                "news",
                f"News **missing candidates** for HKT {day}",
                link=link,
                action="python3 ~/catalyxt.ltd/scripts/run_news_candidates_timer.py",
            )
        )
        todos.append(
            Item(
                "fail",
                "news",
                f"Generate candidates for {day}",
                link=link,
                action="run_news_candidates_timer.py",
            )
        )
    else:
        att.append(Item("attention", "news", f"News state unknown ({state}) {detail}"))
    return well, att, fail, todos


def collect_vault_health(vault: Path | None) -> tuple[list[Item], list[Item], list[Item]]:
    well, att, fail = [], [], []
    if not vault:
        return well, att, fail
    health = vault / "agent-tasks" / "health-status.md"
    text = _read(health)
    if not text:
        att.append(Item("attention", "vault", "health-status.md missing"))
        return well, att, fail
    link = _wiki_link(vault, "agent-tasks/health-status.md", "health-status")
    overall = "unknown"
    m = re.search(r"\*\*Overall\*\*:\s*(\w+)", text)
    if m:
        overall = m.group(1).upper()
    if overall in ("OK", "HEALTHY", "PASS"):
        well.append(Item("green", "vault", f"Vault health **{overall}**", link=link))
    elif overall in ("DEGRADED", "WARN"):
        att.append(
            Item(
                "attention",
                "vault",
                f"Vault health **{overall}**",
                link=link,
                action="See Recommendations in health-status",
            )
        )
    else:
        fail.append(Item("fail", "vault", f"Vault health **{overall}**", link=link))

    # Recommendations table only (cleaner than raw status rows)
    in_rec = False
    for line in text.splitlines():
        if line.startswith("## Recommendations"):
            in_rec = True
            continue
        if in_rec and line.startswith("## "):
            break
        if in_rec and line.strip().startswith("|") and "Conf" not in line and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 4 and cells[1] in ("WARN", "FAIL", "ERROR", "CRIT"):
                att.append(
                    Item(
                        "attention" if cells[1] == "WARN" else "fail",
                        "vault",
                        f"{cells[1]}: {cells[2][:80]} — {cells[3][:60]}",
                        link=link,
                        action=cells[2][:100],
                    )
                )
    return well, att, fail


def collect_kanban(vault: Path | None) -> tuple[list[Item], list[Item]]:
    att, todos = [], []
    if not vault:
        return att, todos
    kanban = vault / "agent-tasks" / "kanban.md"
    text = _read(kanban)
    if not text:
        return att, todos
    link = _wiki_link(vault, "agent-tasks/kanban.md", "kanban")
    section = None
    counts = {"Backlog": 0, "Doing": 0, "Blocked": 0, "Spec": 0}
    open_items: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if section in counts and line.strip().startswith("- [ ]"):
            counts[section] = counts.get(section, 0) + 1
            if section in ("Doing", "Blocked", "Spec") and len(open_items) < 8:
                open_items.append(line.strip()[:100])
    if counts.get("Blocked", 0):
        att.append(
            Item(
                "attention",
                "kanban",
                f"Kanban **Blocked**: {counts['Blocked']}",
                link=link,
                action="Review Blocked section",
            )
        )
    if counts.get("Doing", 0):
        att.append(
            Item(
                "attention",
                "kanban",
                f"Kanban **Doing**: {counts['Doing']}",
                link=link,
            )
        )
    for it in open_items:
        todos.append(Item("attention", "kanban", it, link=link))
    if sum(counts.values()) == 0:
        # still backlog
        if counts.get("Backlog", 0) == 0 and "## Backlog" in text:
            pass
    bl = len(re.findall(r"^- \[ \] ", text, re.M))
    if bl and not todos:
        todos.append(
            Item(
                "info",
                "kanban",
                f"{bl} open checkbox items on kanban",
                link=link,
            )
        )
    return att, todos


def collect_security(quick: bool) -> tuple[list[Item], list[Item], list[Item]]:
    well, att, fail = [], [], []
    # Scan home product roots only by default (fast); optional deep
    roots = [
        Path.home() / "catalyxt.ltd",
        Path.home() / "zk-business-card",
        Path.home() / "email-detach",
        Path.home() / "watchlist",
    ]
    bad_found: list[str] = []
    payload_found: list[str] = []
    for root in roots:
        if not root.is_dir():
            continue
        for lock in root.rglob("package-lock.json"):
            if "node_modules" in lock.parts:
                continue
            try:
                data = json.loads(lock.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            pkgs = data.get("packages") or {}
            for k, v in pkgs.items():
                if not isinstance(v, dict):
                    continue
                name = v.get("name") or k.split("node_modules/")[-1]
                ver = v.get("version") or ""
                if name in MAL_SEED and ver == MAL_SEED[name]:
                    bad_found.append(f"{name}@{ver} in {lock}")
        # payload filenames (shallow)
        if not quick:
            for pat in ("setup.mjs", "Math_Symbol.js", "math_init.js"):
                for p in root.rglob(pat):
                    if "node_modules" in p.parts or ".git" in p.parts:
                        # still report if in node_modules of product
                        payload_found.append(str(p))

    # home-level payload hunt limited
    for pat in ("Math_Symbol.js", "gh-token-monitor.sh", "gh-token-monitor.service"):
        for p in Path.home().glob(pat):
            payload_found.append(str(p))

    if bad_found:
        for b in bad_found[:10]:
            fail.append(
                Item(
                    "fail",
                    "security",
                    f"Malicious npm pin: {b}",
                    action="Isolate host; remove package; rotate credentials",
                )
            )
    if payload_found:
        for p in payload_found[:10]:
            fail.append(
                Item(
                    "fail",
                    "security",
                    f"Payload IoC file: `{p}`",
                    action="Do not execute; quarantine; forensic review",
                )
            )
    if not bad_found and not payload_found:
        well.append(
            Item(
                "green",
                "security",
                "npm keyv/ChainDrop seed scan: **no malicious pins/payloads** in home product trees",
                action="Last check embedded in this dashboard",
            )
        )
    return well, att, fail


def collect_portfolio() -> tuple[list[Item], list[Item]]:
    well, att = [], []
    sot = (HARNESS / "VERSION").read_text(encoding="utf-8").strip() if (HARNESS / "VERSION").is_file() else "?"
    products = HARNESS / "config" / "night_shift_products.yaml"
    lag = []
    if products.is_file():
        for line in products.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            pid, raw = line.split(":", 1)
            pid = pid.strip()
            if pid == "agent-harness":
                continue
            root = Path(os.path.expanduser(raw.strip()))
            hv = root / ".agents" / "HARNESS_VERSION"
            if not hv.is_file():
                lag.append(f"{pid}:missing")
                continue
            v = hv.read_text(encoding="utf-8").lstrip("\ufeff").strip()
            if v != sot:
                lag.append(f"{pid}:{v}")
    if lag:
        att.append(
            Item(
                "attention",
                "portfolio",
                f"Harness lag vs SoT {sot}: {', '.join(lag)}",
                action="python3 scripts/portfolio_install_report.py --install --push",
            )
        )
    else:
        well.append(Item("green", "portfolio", f"All products on harness **{sot}**"))
    return well, att


def build(vault: Path | None, quick: bool) -> Dashboard:
    now = datetime.now(timezone.utc)
    hkt = datetime.now(HKT)
    d = Dashboard(
        when_utc=now.strftime("%Y-%m-%d %H:%M UTC"),
        when_hkt=hkt.strftime("%Y-%m-%d %H:%M HKT"),
        overall="GREEN",
    )
    w, a, f = collect_night(vault, HARNESS)
    d.went_well.extend(w)
    d.attention.extend(a)
    d.failing.extend(f)

    w, a, f, t = collect_news(vault)
    d.went_well.extend(w)
    d.attention.extend(a)
    d.failing.extend(f)
    d.todos.extend(t)

    w, a, f = collect_vault_health(vault)
    d.went_well.extend(w)
    d.attention.extend(a)
    d.failing.extend(f)

    a, t = collect_kanban(vault)
    d.attention.extend(a)
    d.todos.extend(t)

    w, a, f = collect_security(quick=quick)
    d.went_well.extend(w)
    d.attention.extend(a)
    d.failing.extend(f)

    w, a = collect_portfolio()
    d.went_well.extend(w)
    d.attention.extend(a)

    # Night fail tickets as todos
    tickets = HARNESS / ".agents/artifacts/NIGHT_FAIL_TICKETS.md"
    ttext = _read(tickets)
    for line in ttext.splitlines():
        if line.strip().startswith("- [ ]"):
            d.todos.append(
                Item(
                    "fail",
                    "night_shift",
                    line.strip()[6:][:120],
                    action="See NIGHT_FAIL_TICKETS / product TODO",
                )
            )

    if d.failing:
        d.overall = "RED"
    elif d.attention or d.todos:
        d.overall = "ATTENTION"
    else:
        d.overall = "GREEN"
    return d


def render(d: Dashboard, vault: Path | None) -> str:
    emoji = {"GREEN": "🟢", "ATTENTION": "🟡", "RED": "🔴"}.get(d.overall, "⚪")

    def section(title: str, items: list[Item], empty: str) -> list[str]:
        lines = [f"## {title}", ""]
        if not items:
            lines.append(empty)
            lines.append("")
            return lines
        lines.append("| Sev | Area | Summary | Link | Action |")
        lines.append("|-----|------|---------|------|--------|")
        for it in items:
            link = it.link or "—"
            act = it.action.replace("|", "\\|") if it.action else "—"
            lines.append(
                f"| {it.severity} | {it.area} | {it.summary} | {link} | {act} |"
            )
        lines.append("")
        return lines

    lines = [
        "---",
        "tags:",
        "  - type/ops",
        "  - domain/ops",
        "  - dashboard",
        "---",
        "",
        "# OPS DASHBOARD",
        "",
        f"**Overall:** {emoji} **{d.overall}**  ",
        f"**Updated:** {d.when_utc} · {d.when_hkt}  ",
        "**Generator:** `python3 scripts/ops_dashboard.py --write`  ",
        "",
        "> **How to use:** Open this note first every morning.  ",
        "> - 🟢 **GREEN** → nothing required  ",
        "> - 🟡 **ATTENTION** / 🔴 **RED** → use **Link** column, then clear the source so next refresh goes green  ",
        "",
        "## At a glance",
        "",
        "| | Count |",
        "|--|------:|",
        f"| Went well | {len(d.went_well)} |",
        f"| Needs attention | {len(d.attention)} |",
        f"| Failing | {len(d.failing)} |",
        f"| To-do | {len(d.todos)} |",
        "",
    ]
    lines.extend(section("✅ What went well", d.went_well, "_Nothing recorded this run._"))
    lines.extend(
        section(
            "⚠️ Needs attention",
            d.attention,
            "_None — no soft warnings._",
        )
    )
    lines.extend(
        section(
            "❌ Failing (require attention)",
            d.failing,
            "_None — no hard fails._",
        )
    )
    lines.extend(section("☐ To-do", d.todos, "_No open action items from this aggregator._"))

    lines.extend(
        [
            "## Source map (do not hunt 10 pages — start here)",
            "",
            "| Signal | Note |",
            "|--------|------|",
        ]
    )
    if vault:
        lines.extend(
            [
                f"| Night shift multi-product | {_wiki_link(vault, '01-Projects/harness-night-shift/SUMMARY.md', 'harness-night-shift SUMMARY')} |",
                "| Per-product night TODO | `01-Projects/<product>/TODO.md` |",
                "| Catalyxt news inbox | `01-Projects/catalyxt/news-inbox/YYYY-MM-DD` |",
                f"| Vault health | {_wiki_link(vault, 'agent-tasks/health-status.md', 'health-status')} |",
                f"| Hygiene | {_wiki_link(vault, 'agent-tasks/hygiene-status.md', 'hygiene-status')} |",
                f"| Pipeline | {_wiki_link(vault, 'agent-tasks/pipeline-status.md', 'pipeline-status')} |",
                f"| Kanban | {_wiki_link(vault, 'agent-tasks/kanban.md', 'kanban')} |",
                f"| This dashboard | {_wiki_link(vault, 'agent-tasks/OPS-DASHBOARD.md', 'OPS-DASHBOARD')} |",
            ]
        )
    else:
        lines.append("| Vault | not found — set PRODUCT_VAULT_ROOT |")

    lines.extend(
        [
            "",
            "## Refresh commands",
            "",
            "```bash",
            "export PRODUCT_VAULT_ROOT=/opt/second-brain/vault",
            "cd ~/agent-harness",
            "python3 scripts/night_shift_morning_triage.py",
            "python3 scripts/ops_dashboard.py --write",
            "# security deep (optional): python3 scripts/ops_dashboard.py --write  # default includes seed scan",
            "```",
            "",
            "## Regular security check",
            "",
            "This dashboard re-scans home product lockfiles for **keyv/ChainDrop** seed malicious versions "
            "and obvious payload filenames. For root/containerd, re-run occasionally with sudo forensic script.",
            "",
            "_Auto-generated — do not hand-edit the tables; fix sources and re-run generator._",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=None)
    ap.add_argument("--write", action="store_true", default=True)
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--quick", action="store_true", help="Faster security (lockfiles only)")
    ap.add_argument("--stdout", action="store_true")
    args = ap.parse_args(argv)
    vault = _vault_root(args.vault)
    d = build(vault, quick=args.quick)
    md = render(d, vault)
    if args.stdout or args.no_write:
        print(md)
    if not args.no_write:
        if not vault:
            print("ops_dashboard: no vault — printed only", file=sys.stderr)
            print(md)
            return 1
        out = vault / "agent-tasks" / "OPS-DASHBOARD.md"
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(md, encoding="utf-8")
            print(f"ops_dashboard overall={d.overall} wrote={out}")
        except OSError as e:
            # fallback home vault
            alt = Path.home() / "second-brain" / "vault" / "agent-tasks" / "OPS-DASHBOARD.md"
            try:
                alt.parent.mkdir(parents=True, exist_ok=True)
                alt.write_text(md, encoding="utf-8")
                print(f"ops_dashboard overall={d.overall} wrote={alt} (fallback: {e})")
            except OSError as e2:
                print(md)
                print(f"ops_dashboard write failed: {e2}", file=sys.stderr)
                return 1
    return 0 if d.overall != "RED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
