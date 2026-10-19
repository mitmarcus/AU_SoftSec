from datetime import datetime

from payrates import round_quarter, supplement, total_pay


def test_round_quarter():
    assert round_quarter(1.1) == 1.0
    assert round_quarter(1.13) == 1.25
    assert round_quarter(2.875) == 3.0


def test_supplement():
    assert supplement(datetime(2026, 9, 1, 9)) == 0.0  # Tuesday morning
    assert supplement(datetime(2026, 9, 1, 19)) == 0.25  # Tuesday evening
    assert supplement(datetime(2026, 9, 5, 9)) == 0.5  # Saturday


def test_total_pay():
    shifts = [
        (datetime(2026, 9, 1, 8), datetime(2026, 9, 1, 12)),  # 4 h, no supplement
        (datetime(2026, 9, 5, 10), datetime(2026, 9, 5, 12)),  # 2 h, weekend
    ]
    assert total_pay(shifts, 200) == {"hours": 6.0, "pay": 1400.0}
