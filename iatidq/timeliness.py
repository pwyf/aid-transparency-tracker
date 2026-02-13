

TIMELINESS_SCORE_LOOKUP = {
    "monthly": {
        "one month": 1.0,
        "a quarter": 0.963,
        "more than a quarter": 0.813
    },
    "quarterly": {
        "one month": 0.963,
        "a quarter": 0.925,
        "more than a quarter": 0.775
    },
    "less than quarterly": {
        "one month": 0.813,
        "a quarter": 0.775,
        "more than a quarter": 0.625
    },
    "insufficient": {
        "one month": 0,
        "a quarter": 0,
        "more than a quarter": 0
    },
}

def get_timeliness_score(frequency, timelag):
    if frequency is None or timelag is None:
        return None
    return TIMELINESS_SCORE_LOOKUP[frequency][timelag]
