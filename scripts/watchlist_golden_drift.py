#!/usr/bin/env python3
"""Watchlist golden-fixture drift check + re-export remedy (night path).

SoT for the remedy: ~/watchlist/migration/tests/fixtures/golden/README.md
Command when beyond tolerance: php bin/refresh.php --export-golden=TICKER
(from ~/watchlist/migration), drop obsolete same-ticker fixtures, then
vendor/bin/phpunit tests/GoldenFixtureTest.php tests/ParityTest.php and
PYTHONPATH=. pytest tests/test_golden_fixtures.py.

This checker mirrors the ParityTest bands exactly (never wider):
  price  : tol = max(2.0, expected * pct) ; pct = 0.05, 0.15 (age>7), 0.25 (age>14);
           crypto age>14 -> max(pct, 0.45); crypto age>30 -> positive-only check.
  RSI    : tol = max(5.0, 0.12 * expected); age>7 -> max(tol,12); age>14 -> max(tol,25);
           skipped when closes < 50 or (crypto and age > 30).
  SMA50  : tol = max(2.5, 0.015 * expected); age>7 -> +0.04*expected;
           age>14 -> max(tol, 0.10*expected, 38); age>30 -> max(tol, 0.12*expected, 40).

Modes (default is a dry report, never silent widening):
  --dry-run / default : report only. Exit 0 = all inside bands.
                        Exit 2 = at least one metric beyond tolerance (re-export needed).
  --fix               : for each ticker beyond tolerance (or --weekly headroom-poor),
                        run the README remedy: export-golden, drop obsolete
                        same-ticker files, run phpunit + pytest.
  --weekly            : also flag fixtures with < 25% band headroom as
                        re-export candidates (pre-empt the nightly gate).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, UTC
from pathlib import Path

HOME = Path.home()
MIGRATION = HOME / "watchlist" / "migration"
GOLDEN_DIR = MIGRATION / "tests" / "fixtures" / "golden"
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/"
UA = "Mozilla/5.0 (X11; Linux x86_64) watchlist-golden-drift/1.0"
HARNESS_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- tolerances
def is_crypto(ticker: str) -> bool:
    t = ticker.upper()
    return t.startswith(("BTC", "ETH", "SOL")) or "-USD" in t


def price_band(expected: float, age_days: int, ticker: str) -> float | None:
    """Return tolerance or None for the crypto age>30 positive-only check."""
    pct = 0.05
    if age_days > 14:
        pct = 0.25
    elif age_days > 7:
        pct = 0.15
    if is_crypto(ticker):
        if age_days > 30:
            return None  # positive-only: parity gate only asserts price > 0
        if age_days > 14:
            pct = max(pct, 0.45)
    return max(2.0, expected * pct)


def rsi_band(expected: float, age_days: int) -> float:
    tol = max(5.0, expected * 0.12)
    if age_days > 14:
        tol = max(tol, 25.0)
    elif age_days > 7:
        tol = max(tol, 12.0)
    return tol


def sma50_band(expected: float, age_days: int) -> float:
    tol = max(2.5, expected * 0.015)
    if age_days > 30:
        tol = max(tol, expected * 0.12, 40.0)
    elif age_days > 14:
        tol = max(tol, expected * 0.10, 38.0)
    elif age_days > 7:
        tol = max(tol, expected * 0.04)
    return tol


def age_days_of(date_s: str) -> int | None:
    try:
        ts = time.mktime(datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=UTC).timetuple())
    except ValueError:
        return None
    return int((time.time() - ts) // 86400)


# ---------------------------------------------------------------- live data
def fetch_chart(ticker: str, days: int = 200) -> tuple[float | None, list[float]]:
    url = f"{YAHOO_CHART}{ticker}?interval=1d&range={days}d"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://finance.yahoo.com/"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    result = (data.get("chart") or {}).get("result") or [{}]
    r0 = result[0] if result else {}
    meta = r0.get("meta") or {}
    price = meta.get("regularMarketPrice")
    quote = ((r0.get("indicators") or {}).get("quote") or [{}])[0]
    raw = quote.get("close") or []
    closes = [float(c) for c in raw if c is not None]
    # Mirror the PHP trailing-null fill: equities leave the live bar null for
    # ~24h; regularMarketPrice is the real trailing close, a mid-hole is not.
    if raw and raw[-1] is None and price is not None:
        closes.append(float(price))
    return (float(price) if price is not None else None), closes


def wilder_rsi(closes: list[float], period: int = 14) -> float | None:
    n = len(closes)
    if n < 2:
        return None
    period = min(period, n - 1)
    changes = [closes[i] - closes[i - 1] for i in range(1, n)]
    use = min(period, len(changes))
    gain = sum(c for c in changes[:use] if c > 0)
    loss = sum(-c for c in changes[:use] if c < 0)
    avg_gain, avg_loss = gain / use, loss / use
    for c in changes[use:]:
        g = c if c > 0 else 0.0
        loss_c = -c if c < 0 else 0.0
        avg_gain = (avg_gain * (use - 1) + g) / use
        avg_loss = (avg_loss * (use - 1) + loss_c) / use
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


# ---------------------------------------------------------------- fixtures
def load_fixtures() -> list[dict]:
    rows = []
    for f in sorted(GOLDEN_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("ticker"):
            rows.append({"file": f, **data})
    return rows


def check_ticker(row: dict, *, weekly: bool) -> dict:
    ticker = row["ticker"]
    date_s = row.get("date") or ""
    age = age_days_of(date_s) if date_s else None
    out: dict = {"ticker": ticker, "file": row["file"].name, "date": date_s,
                 "age_days": age, "breach": [], "warn": [], "skip": []}
    if age is None:
        out["skip"].append("bad/missing date")
        return out
    try:
        price, closes = fetch_chart(ticker)
    except Exception as exc:  # noqa: BLE001 — report, do not crash the night run
        out["skip"].append(f"live fetch failed: {exc}")
        return out
    out["live_price"] = price
    out["closes"] = len(closes)

    exp_price = row.get("price")
    if exp_price is not None and price is not None:
        band = price_band(float(exp_price), age, ticker)
        if band is None:
            out["skip"].append("price: crypto age>30 positive-only")
        else:
            delta = abs(float(price) - float(exp_price))
            out["price_delta"] = round(delta, 4)
            out["price_band"] = round(band, 4)
            if delta > band:
                out["breach"].append(f"price {price} vs {exp_price} delta {delta:.2f} > {band:.2f}")
            elif weekly and (band - delta) / band < 0.25:
                out["warn"].append(f"price headroom {(band - delta) / band:.0%} < 25%")

    exp_rsi = row.get("rsi")
    if exp_rsi is not None and len(closes) > 14:
        if len(closes) < 50 or (is_crypto(ticker) and age > 30):
            out["skip"].append("rsi: series/age rule")
        else:
            live = wilder_rsi(closes[-80:] if len(closes) > 80 else closes)
            band = rsi_band(float(exp_rsi), age)
            out["live_rsi"] = live
            out["rsi_band"] = round(band, 4)
            if live is not None:
                delta = abs(live - float(exp_rsi))
                out["rsi_delta"] = round(delta, 4)
                if delta > band:
                    out["breach"].append(f"rsi {live} vs {exp_rsi} delta {delta:.2f} > {band:.2f}")
                elif weekly and (band - delta) / band < 0.25:
                    out["warn"].append(f"rsi headroom {(band - delta) / band:.0%} < 25%")

    exp_sma = row.get("sma50")
    if exp_sma is not None and len(closes) > 50:
        live = sum(closes[-50:]) / 50.0
        band = sma50_band(float(exp_sma), age)
        out["live_sma50"] = round(live, 4)
        out["sma_band"] = round(band, 4)
        delta = abs(live - float(exp_sma))
        out["sma_delta"] = round(delta, 4)
        if delta > band:
            out["breach"].append(f"sma50 {live:.2f} vs {exp_sma} delta {delta:.2f} > {band:.2f}")
        elif weekly and (band - delta) / band < 0.25:
            out["warn"].append(f"sma50 headroom {(band - delta) / band:.0%} < 25%")
    return out


# ---------------------------------------------------------------- remedy
def remedy(tickers: list[str]) -> int:
    rc = 0
    for t in tickers:
        print(f"[golden] re-exporting {t} via README remedy …", flush=True)
        r = subprocess.run(
            ["php", "bin/refresh.php", f"--export-golden={t}"],
            cwd=str(MIGRATION), capture_output=True, text=True, timeout=600,
        )
        print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
        if r.returncode != 0:
            print(f"[golden] FAIL export-golden {t} exit {r.returncode}", flush=True)
            rc = r.returncode
            continue
        # Newest by date-in-name wins; drop everything older for this ticker.
        dated = []
        for p in GOLDEN_DIR.glob(f"{t.lower()}_*.json"):
            try:
                dated.append((datetime.strptime(p.stem.split("_", 1)[1], "%Y-%m-%d"), p))
            except ValueError:
                continue
        dated.sort()
        for _, p in dated[:-1]:
            print(f"[golden] dropping obsolete {p.name}", flush=True)
            p.unlink()
        for cmd in (
            ["vendor/bin/phpunit", "tests/GoldenFixtureTest.php", "tests/ParityTest.php"],
            [sys.executable, "-m", "pytest", "tests/test_golden_fixtures.py"],
        ):
            env_cmd = cmd if cmd[0] != sys.executable else [sys.executable, "-m", "pytest", "tests/test_golden_fixtures.py"]
            r2 = subprocess.run(env_cmd, cwd=str(MIGRATION), capture_output=True, text=True, timeout=1200)
            print(f"[golden] {' '.join(env_cmd[-2:])} exit {r2.returncode}", flush=True)
            print((r2.stdout or "")[-1500:], (r2.stderr or "")[-800:], flush=True)
            if r2.returncode != 0:
                rc = r2.returncode
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--fix", action="store_true", help="run the README remedy for breaching tickers")
    ap.add_argument("--weekly", action="store_true", help="also flag <25% headroom fixtures")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--fixtures-dir", type=Path, default=None, help="override golden dir (tests)")
    args = ap.parse_args(argv)
    global GOLDEN_DIR
    if args.fixtures_dir:
        GOLDEN_DIR = args.fixtures_dir

    rows = load_fixtures()
    if not rows:
        print(f"[golden] no fixtures under {GOLDEN_DIR}")
        return 0
    reports = [check_ticker(r, weekly=args.weekly) for r in rows]

    if args.json:
        print(json.dumps(reports, indent=2, default=str))
    else:
        for rep in reports:
            line = (f"[golden] {rep['ticker']} {rep['date']} age={rep['age_days']}d "
                    f"priceΔ={rep.get('price_delta', '-')} band={rep.get('price_band', '-')} "
                    f"rsiΔ={rep.get('rsi_delta', '-')} band={rep.get('rsi_band', '-')} "
                    f"sma50Δ={rep.get('sma_delta', '-')} band={rep.get('sma_band', '-')}")
            print(line, flush=True)
            for b in rep["breach"]:
                print(f"[golden]   BEYOND TOLERANCE: {b}", flush=True)
            for w in rep["warn"]:
                print(f"[golden]   headroom warn: {w}", flush=True)
            for s in rep["skip"]:
                print(f"[golden]   skip: {s}", flush=True)

    need = [rep["ticker"] for rep in reports if rep["breach"]]
    if args.weekly:
        need += [rep["ticker"] for rep in reports if rep["warn"] and rep["ticker"] not in need]
    need = sorted(set(need))
    if not need:
        print("[golden] all fixtures inside ParityTest bands — no re-export needed")
        return 0
    if not args.fix:
        print(f"[golden] WOULD RE-EXPORT (dry run, remedy = php bin/refresh.php --export-golden=T): {', '.join(need)}")
        return 2
    return remedy(need)


if __name__ == "__main__":
    sys.exit(main())
