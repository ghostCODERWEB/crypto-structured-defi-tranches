"""Replay gains and losses through senior coupon and junior first-loss capital with insolvency accounting."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    senior = integer(d["senior"])
    junior = integer(d["junior"])
    coupon = integer(d["senior_coupon"])
    initial = senior + junior
    trace = []
    bad_debt = 0
    for e in chronology(d["events"]):
        amount = integer(e["amount"])
        kind = e["kind"]
        if kind == "gain":
            to_senior = min(amount, coupon)
            senior += to_senior
            junior += amount - to_senior
        elif kind == "loss":
            junior_loss = min(junior, amount)
            junior -= junior_loss
            rest = amount - junior_loss
            senior_loss = min(senior, rest)
            senior -= senior_loss
            bad_debt += rest - senior_loss
        else:
            raise ValueError("unknown event")
        trace.append(
            {
                "timestamp": e["timestamp"],
                "senior": senior,
                "junior": junior,
                "unabsorbed_loss": bad_debt,
            }
        )
    return {
        "senior": senior,
        "junior": junior,
        "unabsorbed_loss": bad_debt,
        "capital_change": senior + junior - initial,
        "trace": trace,
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
