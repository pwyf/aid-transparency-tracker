import pytest

from iatidataquality import db
from iatidq import models


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
        db.session.add(org)


def test_organisations_page(client, organisation_in_db):
    response = client.get("/organisations/")
    assert response.status_code == 200
    assert b"Example Org" in response.data


def test_organisation_page(client, as_admin, organisation_in_db):
    response = client.get("/organisations/XE-EXAMPLE-1/index/")
    assert response.status_code == 200
    assert b"Publication" in response.data
    assert b"Example Org" in response.data
