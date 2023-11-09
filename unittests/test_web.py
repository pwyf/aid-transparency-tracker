import re

import pytest

from iatidataquality import db
from iatidq import models


def remove_tags(text):
    return re.sub("<[^<]+?>", "", text)


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Aid Transparency Tracker" in response.data


@pytest.fixture
def organisation_in_db():
    with db.session.begin():
        org = models.Organisation()
        org.setup(
            organisation_name="Example Org",
            registry_slug="example_org",
            organisation_code="XE-EXAMPLE-1",
            organisation_total_spend=0,
        )
        org.frequency = "quarterly"
        org.timelag = "more than a quarter"
        db.session.add(org)


def test_organisations_page(client, organisation_in_db):
    response = client.get("/organisations/")
    assert response.status_code == 200
    assert b"Example Org" in response.data


def test_organisation_index(client, as_admin, organisation_in_db, mocker):
    mocker.patch(
        "iatidataquality.organisations.get_summary_data", return_value=(43.1, 35)
    )

    response = client.get("/organisations/XE-EXAMPLE-1/index/")
    assert response.status_code == 200

    assert "Publication" in response.text
    assert "Example Org" in response.text

    text_without_tags = remove_tags(response.text)
    assert re.search("Publishing frequency:[ \n\t]*quarterly", text_without_tags)
    assert re.search("Time lag:[ \n\t]*more than a quarter", text_without_tags)


@pytest.fixture
def organisation_indicators_split_mock(mocker):
    mocker.patch(
        "iatidq.dqorganisations._organisation_indicators_split",
        return_value={
            "commitment": {},
            "zero": {},
            "non_zero": {
                1: {
                    "indicator": {
                        "id": 1,
                        "name": "example-indicator",
                        "description": "Example indicator",
                        "long_description": "Example indicator more information",
                        "indicator_order": 1,
                        "indicator_category_name": "activity",
                        "indicator_subcategory_name": "subcategory_name",
                        "indicator_weight": 1.0,
                    },
                    "results_pct": 60.0,
                    "tests": [
                        {
                            "test": {
                                "id": 1,
                                "name": "Gherkin",
                            },
                            "results_pct": 60.0,
                            "results_num": 5,
                        }
                    ],
                }
            },
        },
    )


def test_organisation_publication_page(
    client, as_admin, organisation_in_db, organisation_indicators_split_mock
):
    response = client.get("/organisations/XE-EXAMPLE-1/publication/")
    assert response.status_code == 200

    assert (
        '<p class="lead">It looks like you publish quarterly with a time lag of more than a quarter, so the maximum you can score for IATI data is 87.5 points. The total points for the relevant indicators have been adjusted accordingly.</p>'
        in response.text
    )

    expected_table = """
          <table class="table">
          <thead>
              <th colspan="3">Data quality score calculation</th>
          </thead>
          <tbody>
          <tr>
              <td>Data quality</td>
              <td>60.0%</td>
              <td>% of activities that passed tests</td>
          </tr>
          <tr class="text-muted">
              <td>Convert percentage to points</td><td>÷ 1.5</td>
              <td></td>
          </tr>
          <tr>
              <td>Points</td>
              <td>40.0</td>
              <td></td>
          </tr>

          <tr class="text-muted">
              <td>Timeliness</td>
            <td>x 0.813 (It looks like you publish quarterly with a time lag of more than a quarter, so the maximum you can score for IATI data is 87.5 points. The total points for the relevant indicators have been adjusted accordingly.)</td>
              <td>(Updated quarterly and with more than a quarter) time lag</td>
          </tr>

          <tr>
              <td><strong>Total data quality points</strong></td>
              <td>32.52</td><td></td>
          </tr>
          </tbody>
          </table>
          <table class="table">
          <thead>
              <th colspan="3">Total score calculation</th>
          </thead>
          <tbody>
          <tr>
              <td>Data quality points</td><td>32.52</td>
              <td></td>
          </tr>
          <tr>
              <td>Publication format points</td><td>33.33</td>
              <td></td>
          </tr>
          <tr class="success">
              <td><strong>Total points for this indicator</strong></td>
              <td>65.85</td><td></td>
          </tr>
          </tbody>
          </table>
    """

    assert re.sub("[ \t\n]+", " ", expected_table) in re.sub(
        "[ \t\n]+", " ", response.text
    )


def test_csv(client, as_admin, organisation_in_db, organisation_indicators_split_mock):
    response = client.get("/organisations/publication_index_history.csv")
    assert response.status_code == 200
    response = client.get("/organisations/publication_index.csv")
    assert response.status_code == 200
    response = client.get("/organisations/publication.csv")
    assert response.status_code == 200
    response = client.get("/organisations/XE-EXAMPLE-1/publication.csv")
    assert response.status_code == 200
