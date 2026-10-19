"""Pay calculation for cleaning shifts."""

import math

EVENING_FROM = 18
EVENING_UNTIL = 6
EVENING_SUPPLEMENT = 0.25
WEEKEND_SUPPLEMENT = 0.50


def round_quarter(hours):
    """Round hours to the nearest quarter hour."""
    return math.floor(hours * 4 + 0.5) / 4


def supplement(start):
    """Extra pay factor for a shift that starts at `start`."""
    if start.weekday() >= 5:
        return WEEKEND_SUPPLEMENT
    if start.hour >= EVENING_FROM or start.hour < EVENING_UNTIL:
        return EVENING_SUPPLEMENT
    return 0.0


def total_pay(shifts, hourly_rate):
    """Total hours and pay for a list of (start, end) datetime pairs."""
    hours = 0.0
    pay = 0.0
    for start, end in shifts:
        shift_hours = round_quarter((end - start).total_seconds() / 3600)
        hours += shift_hours
        pay += shift_hours * hourly_rate * (1 + supplement(start))
    return {"hours": hours, "pay": round(pay, 2)}
