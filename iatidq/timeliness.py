

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
}

def get_timeliness_score(frequency, timelag):
    return TIMELINESS_SCORE_LOOKUP[frequency][timelag]
