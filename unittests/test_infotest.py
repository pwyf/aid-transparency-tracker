"""Tests for beta/infotest.py — the four per-org infotest functions.

Fixtures live under unittests/fixtures/iati_data/2024-01-01/ and represent
slim Belgium DGD (be-dgd / XM-DAC-2-10) data:
  - be-dgd-activities.xml: two activities (AF with A09 doc-link; AO with no A09)
  - be-dgd-org.xml: one organisation with B03 for AO and disaggregated budgets
    for AF (3 years forward) and DZ (1 year forward only)

SNAPSHOT_DATE is 2024-01-01 so budget period-end dates can be fixed in the XML.

The module-level current_country_codes_by_org* dicts are monkeypatched per
test to a small set {AF, DZ, AO} so assertions stay manageable.
"""

import csv
import os
from dataclasses import dataclass
from os.path import abspath, dirname, join

import iatikit
import pytest

from beta import infotest
from iatidataquality import app as flask_app

SNAPSHOT_DATE = "2024-01-01"
FIXTURES_DIR = join(dirname(abspath(__file__)), "fixtures", "iati_data")
ORG_CODE = "XM-DAC-2-10"
REGISTRY_SLUG = "be-dgd"
SELF_REF = "XM-DAC-2-10"
TEST_COUNTRIES = frozenset({"AF", "DZ", "AO"})
CURRENT_DATA_RESULTS = {"be-dgd-activities": {0: True, 1: True}}


@dataclass
class MockOrg:
    organisation_code: str
    registry_slug: str
    condition: str | None
    self_ref: str | None


@pytest.fixture
def org():
    return MockOrg(
        organisation_code=ORG_CODE,
        registry_slug=REGISTRY_SLUG,
        condition=None,
        self_ref=SELF_REF,
    )


@pytest.fixture
def iati_app(tmp_path, monkeypatch):
    """App context with IATI_DATA_PATH → fixtures, IATI_RESULT_PATH → tmp_path.

    iatikit.codelists() is patched to return None because codelists are not
    downloaded in CI. The disaggregated_budget step definitions receive codelists
    as a **kwargs argument but the "available N years forward" step doesn't use it.
    """
    monkeypatch.setitem(flask_app.config, "IATI_DATA_PATH", FIXTURES_DIR)
    monkeypatch.setitem(flask_app.config, "IATI_RESULT_PATH", str(tmp_path))
    monkeypatch.setattr(iatikit, "codelists", lambda: None)
    os.makedirs(join(str(tmp_path), SNAPSHOT_DATE, ORG_CODE), exist_ok=True)
    with flask_app.app_context():
        yield flask_app, tmp_path


def _read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _result_path(tmp_path, filename):
    return join(str(tmp_path), SNAPSHOT_DATE, ORG_CODE, filename)


# ─── country_strategy_or_mou ───────────────────────────────────────────────


class TestCountryStrategyOrMou:
    TEST_NAME = "Strategy (country/sector) or Memorandum of Understanding"
    CSV_NAME = "strategy__country_sector__or_memorandum_of_understanding.csv"

    def _run(self, iati_app, org, current_data_results):
        app, tmp_path = iati_app
        infotest.country_strategy_or_mou(
            org, SNAPSHOT_DATE, self.TEST_NAME, current_data_results
        )
        return _read_csv(_result_path(tmp_path, self.CSV_NAME))

    def _by_country(self, rows):
        """Index rows by country code (last word of explanation)."""
        return {row["explanation"].split()[-1]: row for row in rows}

    def test_activity_a09_found(self, iati_app, org, monkeypatch):
        """Activity with A09 doc-link is written as result '1'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org_country_strategy_exclusions,
            ORG_CODE,
            set(TEST_COUNTRIES),
        )
        rows = self._run(iati_app, org, CURRENT_DATA_RESULTS)
        by_country = self._by_country(rows)
        assert by_country["AF"]["result"] == "1"
        assert "A09" in by_country["AF"]["explanation"]

    def test_org_b03_found(self, iati_app, org, monkeypatch):
        """Org file with B03 doc-link is written as result '1'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org_country_strategy_exclusions,
            ORG_CODE,
            set(TEST_COUNTRIES),
        )
        rows = self._run(iati_app, org, CURRENT_DATA_RESULTS)
        by_country = self._by_country(rows)
        assert by_country["AO"]["result"] == "1"
        assert "B03 or B13" in by_country["AO"]["explanation"]

    def test_no_strategy_gives_zero(self, iati_app, org, monkeypatch):
        """Country with neither A09 nor B03/B13 is written as result '0'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org_country_strategy_exclusions,
            ORG_CODE,
            set(TEST_COUNTRIES),
        )
        rows = self._run(iati_app, org, CURRENT_DATA_RESULTS)
        by_country = self._by_country(rows)
        assert by_country["DZ"]["result"] == "0"
        assert "No country strategy" in by_country["DZ"]["explanation"]

    def test_activity_skipped_when_not_in_current_data(
        self, iati_app, org, monkeypatch
    ):
        """Activity-level A09 is not counted when current_data_results excludes it."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org_country_strategy_exclusions,
            ORG_CODE,
            {"AF"},
        )
        # empty current_data_results: no activity passes the filter
        rows = self._run(iati_app, org, {})
        assert len(rows) == 1
        assert rows[0]["result"] == "0"

    def test_output_has_one_row_per_country(self, iati_app, org, monkeypatch):
        monkeypatch.setitem(
            infotest.current_country_codes_by_org_country_strategy_exclusions,
            ORG_CODE,
            set(TEST_COUNTRIES),
        )
        rows = self._run(iati_app, org, CURRENT_DATA_RESULTS)
        assert len(rows) == len(TEST_COUNTRIES)


# ─── disaggregated_budget ──────────────────────────────────────────────────


class TestDisaggregatedBudget:
    TEST_NAME = "Disaggregated budget"
    CSV_NAME = "disaggregated_budget.csv"

    def _run(self, iati_app, org):
        app, tmp_path = iati_app
        infotest.disaggregated_budget(
            org, SNAPSHOT_DATE, self.TEST_NAME, {}, org.condition
        )
        return _read_csv(_result_path(tmp_path, self.CSV_NAME))

    def _by_country_year(self, rows):
        """Return dict keyed by (country_code, year_number)."""
        result = {}
        for row in rows:
            expl = row["explanation"]
            # "Budget for AF found 1 year forward"  or  "Budget for DZ not found 2 years forward"
            parts = expl.split()
            country = parts[2]
            year = int(parts[-3])
            result[(country, year)] = row
        return result

    def test_af_budget_all_three_years(self, iati_app, org, monkeypatch):
        """AF has budgets covering years 1, 2, 3 forward → all '1'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org, ORG_CODE, set(TEST_COUNTRIES)
        )
        by = self._by_country_year(self._run(iati_app, org))
        assert by[("AF", 1)]["result"] == "1"
        assert by[("AF", 2)]["result"] == "1"
        assert by[("AF", 3)]["result"] == "1"

    def test_dz_budget_only_year_one(self, iati_app, org, monkeypatch):
        """DZ has budget only for year 1 → '1', years 2 and 3 → '0'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org, ORG_CODE, set(TEST_COUNTRIES)
        )
        by = self._by_country_year(self._run(iati_app, org))
        assert by[("DZ", 1)]["result"] == "1"
        assert by[("DZ", 2)]["result"] == "0"
        assert by[("DZ", 3)]["result"] == "0"

    def test_ao_no_budget(self, iati_app, org, monkeypatch):
        """AO has no budget → all three years '0'."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org, ORG_CODE, set(TEST_COUNTRIES)
        )
        by = self._by_country_year(self._run(iati_app, org))
        assert by[("AO", 1)]["result"] == "0"
        assert by[("AO", 2)]["result"] == "0"
        assert by[("AO", 3)]["result"] == "0"

    def test_output_has_three_rows_per_country(self, iati_app, org, monkeypatch):
        """Three rows (years 1-3) are written for each country."""
        monkeypatch.setitem(
            infotest.current_country_codes_by_org, ORG_CODE, set(TEST_COUNTRIES)
        )
        rows = self._run(iati_app, org)
        assert len(rows) == len(TEST_COUNTRIES) * 3

    def test_condition_filters_organisation(self, iati_app, monkeypatch):
        """An org_condition that doesn't match skips the organisation."""
        monkeypatch.setitem(infotest.current_country_codes_by_org, ORG_CODE, {"AF"})
        # Condition with org_condition that matches nothing
        filtered_org = MockOrg(
            organisation_code=ORG_CODE,
            registry_slug=REGISTRY_SLUG,
            condition="|organisation-identifier[.='DOES-NOT-EXIST']",
            self_ref=SELF_REF,
        )
        app, tmp_path = iati_app
        infotest.disaggregated_budget(
            filtered_org, SNAPSHOT_DATE, self.TEST_NAME, {}, filtered_org.condition
        )
        rows = _read_csv(_result_path(tmp_path, self.CSV_NAME))
        assert rows == []


# ─── networked_data_part_2 ─────────────────────────────────────────────────


class TestNetworkedDataPart2:
    TEST_NAME = "Participating Orgs"
    CSV_NAME = "participating_orgs.csv"

    def _run(self, iati_app, org):
        app, tmp_path = iati_app
        infotest.networked_data_part_2(
            org,
            SNAPSHOT_DATE,
            self.TEST_NAME,
            CURRENT_DATA_RESULTS,
            condition=org.condition,
        )
        return _read_csv(_result_path(tmp_path, self.CSV_NAME))

    def test_mixed_refs_score(self, iati_app, org):
        """Activity with 1 known + 1 unknown non-self-ref gets score 0.5."""
        rows = {r["identifier"]: r for r in self._run(iati_app, org)}
        assert rows["BE-DGD-ACT-1"]["result"] == "0.5"
        assert "score:" in rows["BE-DGD-ACT-1"]["explanation"]

    def test_all_self_refs_not_relevant(self, iati_app, org):
        """Activity with only self-ref participating-orgs gets 'not relevant'."""
        rows = {r["identifier"]: r for r in self._run(iati_app, org)}
        assert rows["BE-DGD-ACT-2"]["result"] == "not relevant"
        assert rows["BE-DGD-ACT-2"]["explanation"] == "All self refs"

    def test_activity_skipped_when_not_in_current_data(self, iati_app, org):
        """Activities absent from current_data_results are not written to output."""
        app, tmp_path = iati_app
        infotest.networked_data_part_2(
            org, SNAPSHOT_DATE, self.TEST_NAME, {}, condition=org.condition
        )
        rows = _read_csv(_result_path(tmp_path, self.CSV_NAME))
        assert rows == []

    def test_output_fieldnames(self, iati_app, org):
        rows = self._run(iati_app, org)
        expected = {
            "dataset",
            "identifier",
            "index",
            "result",
            "hierarchy",
            "explanation",
        }
        assert set(rows[0].keys()) == expected


# ─── networked_data_part_3 ─────────────────────────────────────────────────


class TestNetworkedDataPart3:
    TEST_NAME = "Transactions with valid receiver"
    CSV_NAME = "transactions_with_valid_receiver.csv"

    def _run(self, iati_app, org):
        app, tmp_path = iati_app
        infotest.networked_data_part_3(
            org, SNAPSHOT_DATE, self.TEST_NAME, CURRENT_DATA_RESULTS
        )
        return _read_csv(_result_path(tmp_path, self.CSV_NAME))

    def test_mixed_transactions_score(self, iati_app, org):
        """Activity with 1 valid + 1 invalid receiver gets score 0.5."""
        rows = {r["identifier"]: r for r in self._run(iati_app, org)}
        assert rows["BE-DGD-ACT-1"]["result"] == "0.5"
        assert "1" in rows["BE-DGD-ACT-1"]["explanation"]
        assert "2" in rows["BE-DGD-ACT-1"]["explanation"]

    def test_no_transactions_not_relevant(self, iati_app, org):
        """Activity with no transactions gets 'not relevant'."""
        rows = {r["identifier"]: r for r in self._run(iati_app, org)}
        assert rows["BE-DGD-ACT-2"]["result"] == "not relevant"
        assert "No assessable transactions" in rows["BE-DGD-ACT-2"]["explanation"]

    def test_activity_skipped_when_not_in_current_data(self, iati_app, org):
        """Activities absent from current_data_results are not written to output."""
        app, tmp_path = iati_app
        infotest.networked_data_part_3(org, SNAPSHOT_DATE, self.TEST_NAME, {})
        rows = _read_csv(_result_path(tmp_path, self.CSV_NAME))
        assert rows == []

    def test_output_has_two_rows(self, iati_app, org):
        rows = self._run(iati_app, org)
        assert len(rows) == 2
