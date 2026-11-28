"""Forward-dated rows are left out and implausible figures are flagged, never altered."""
import pandas as pd
import pytest

import screener_rag as R


def test_unfinished_financial_years_are_dropped_and_missing_dates_kept():
    d = pd.DataFrame({"name": ["done", "future", "unknown"],
                      "fy_end": ["2026-03-31", "2026-12-31", None],
                      "close_date": ["2026-07-23"] * 3})
    kept, dropped = R._drop_unfinished_years(d)
    assert list(kept["name"]) == ["done", "unknown"] and dropped == 1
    assert R._drop_unfinished_years(d[["name"]])[1] == 0


@pytest.mark.parametrize("row,market,expected", [
    ({"pe": 12, "pb": 2, "roe": 0.2}, "IN", ""),
    ({"pe": 3, "pb": 2, "roe": 0.2}, "IN", "check PE"),
    ({"pe": 3, "pb": 2, "roe": 0.2}, "KR", ""),
    ({"pe": 12, "pb": 80, "roe": 37.4}, "US", "check PB, check ROE"),
    ({"pe": None, "pb": None, "roe": None, "eps": 1.7e-6}, "IN", "check EPS units"),
])
def test_quality_flags(row, market, expected):
    assert R._quality_flags(pd.Series(row), market) == expected
