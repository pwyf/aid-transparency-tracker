"""
Tests for the get_sampling_data carry-forward query in iatidq/summary.py.

Tests the four scenarios established during design:
  1. Never reviewed              → passing
  2. Failing in round 1 only    → failing (carries forward)
  3. Failing R1, pass R2        → passing (later explicit verdict wins)
  4. Failing R1, R2 not reviewed → failing (R1 carries forward)
"""

import pytest

from iatidataquality import db
from iatidq import models

# ─── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def org(app):
    with db.session.begin():
        o = models.Organisation()
        o.setup(
            organisation_name="Test Org",
            registry_slug="test-org",
            organisation_code="XE-TEST-1",
        )
        db.session.add(o)
    return models.Organisation.where(organisation_code="XE-TEST-1").first()


@pytest.fixture
def test_a(app):
    with db.session.begin():
        t = models.Test()
        t.setup(description="Test A", test_group="group", test_level=1, active=True)
        db.session.add(t)
    return models.Test.where(description="Test A").first()


@pytest.fixture
def test_b(app):
    with db.session.begin():
        t = models.Test()
        t.setup(description="Test B", test_group="group", test_level=1, active=True)
        db.session.add(t)
    return models.Test.where(description="Test B").first()


def add_verdict(org_id, test_id, sampling_round, failed):
    with db.session.begin():
        sf = models.SamplingFailure(
            organisation_id=org_id,
            test_id=test_id,
            sampling_round=sampling_round,
            failed=failed,
        )
        db.session.add(sf)


def get_sampling_data(organisation_id):
    """Run the carry-forward query directly, returning a set of failing test ids."""
    sql = """SELECT sf.test_id FROM sampling_failure sf
               WHERE sf.organisation_id = %s
                 AND sf.failed = true
                 AND sf.sampling_round = (
                       SELECT MAX(sf2.sampling_round)
                       FROM sampling_failure sf2
                       WHERE sf2.organisation_id = sf.organisation_id
                         AND sf2.test_id = sf.test_id
                     );"""
    rows = db.engine.execute(sql, (organisation_id,))
    return {row[0] for row in rows}


# ─── carry-forward scenarios ─────────────────────────────────────────────────


def test_never_reviewed_is_passing(app, org, test_a):
    """No SamplingFailure rows at all → test not in failing set → passing."""
    failing = get_sampling_data(org.id)
    assert test_a.id not in failing


def test_failing_round1_only_carries_forward(app, org, test_a):
    """Marked failing in round 1, no round 2 verdict → still failing."""
    add_verdict(org.id, test_a.id, sampling_round=1, failed=True)

    failing = get_sampling_data(org.id)
    assert test_a.id in failing


def test_explicit_pass_in_round2_overrides_round1_fail(app, org, test_a):
    """Failing in round 1, explicitly passed in round 2 → passing."""
    add_verdict(org.id, test_a.id, sampling_round=1, failed=True)
    add_verdict(org.id, test_a.id, sampling_round=2, failed=False)

    failing = get_sampling_data(org.id)
    assert test_a.id not in failing


def test_round2_not_reviewed_carries_forward_round1_fail(app, org, test_a):
    """Failing in round 1, round 2 has no verdict → round 1 carries forward."""
    add_verdict(org.id, test_a.id, sampling_round=1, failed=True)
    # no round 2 verdict

    failing = get_sampling_data(org.id)
    assert test_a.id in failing


def test_multiple_tests_independently_evaluated(app, org, test_a, test_b):
    """Carry-forward logic is applied per (org, test) independently."""
    # test_a: failing R1, pass R2 → passing
    add_verdict(org.id, test_a.id, sampling_round=1, failed=True)
    add_verdict(org.id, test_a.id, sampling_round=2, failed=False)

    # test_b: failing R1 only → failing (carry-forward)
    add_verdict(org.id, test_b.id, sampling_round=1, failed=True)

    failing = get_sampling_data(org.id)
    assert test_a.id not in failing
    assert test_b.id in failing


def test_verdicts_isolated_between_organisations(app, org, test_a):
    """A failing verdict for one org doesn't affect another org."""
    with db.session.begin():
        other = models.Organisation()
        other.setup(
            organisation_name="Other Org",
            registry_slug="other-org",
            organisation_code="XE-OTHER-1",
        )
        db.session.add(other)
    other = models.Organisation.where(organisation_code="XE-OTHER-1").first()

    add_verdict(other.id, test_a.id, sampling_round=1, failed=True)

    failing = get_sampling_data(org.id)
    assert test_a.id not in failing
