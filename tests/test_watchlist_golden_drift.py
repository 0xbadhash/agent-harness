"""Golden drift checker: ParityTest bands must be mirrored exactly (never wider)."""
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "watchlist_golden_drift",
    Path(__file__).resolve().parent.parent / "scripts" / "watchlist_golden_drift.py",
)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


def test_price_bands_match_paritytest():
    # fresh fixture: 5% floor $2
    assert mod.price_band(100.0, 0, "TSLA") == pytest.approx(5.0)
    assert mod.price_band(10.0, 3, "TSLA") == pytest.approx(2.0)  # floor
    assert mod.price_band(100.0, 8, "TSLA") == pytest.approx(15.0)
    assert mod.price_band(100.0, 20, "TSLA") == pytest.approx(25.0)
    # crypto age>30: positive-only (no level band)
    assert mod.price_band(70000.0, 31, "BTC-USD") is None
    # crypto age>14..30: at least 45%
    assert mod.price_band(70000.0, 20, "BTC-USD") == pytest.approx(31500.0)
    assert mod.price_band(70000.0, 8, "BTC-USD") == pytest.approx(10500.0)  # age>7: 15%
    assert mod.price_band(70000.0, 5, "BTC-USD") == pytest.approx(3500.0)


def test_rsi_bands_match_paritytest():
    assert mod.rsi_band(50.0, 0) == pytest.approx(6.0)   # max(5, 12%)
    assert mod.rsi_band(20.0, 0) == pytest.approx(5.0)   # floor
    assert mod.rsi_band(50.0, 8) == pytest.approx(12.0)
    assert mod.rsi_band(50.0, 20) == pytest.approx(25.0)


def test_sma50_bands_match_paritytest():
    assert mod.sma50_band(200.0, 0) == pytest.approx(3.0)   # max(2.5, 1.5%)
    assert mod.sma50_band(100.0, 0) == pytest.approx(2.5)   # floor
    assert mod.sma50_band(200.0, 8) == pytest.approx(8.0)   # +4%
    assert mod.sma50_band(200.0, 20) == pytest.approx(38.0)
    assert mod.sma50_band(200.0, 40) == pytest.approx(40.0)  # max(24, 40)


def test_wilder_rsi_known_series():
    # All gains -> 100; flat -> neutral midpoint via 50.0 guard is n<2 only
    assert mod.wilder_rsi([1.0, 2.0, 3.0, 4.0]) == 100.0
    assert mod.wilder_rsi([5.0]) is None


def test_is_crypto():
    assert mod.is_crypto("BTC-USD")
    assert mod.is_crypto("sol")
    assert not mod.is_crypto("NVDA")