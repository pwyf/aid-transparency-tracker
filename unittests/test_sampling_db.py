"""
Tests for iatidq/sample_work/db.py — the SQLite sampling database layer.

All tests use a temporary file-backed SQLite database so they don't affect
the real sample_work.db. The `sampling_db` fixture populates
app.config['SAMPLING_DB_FILENAME'] for the duration of each test.
"""

import os
from sqlite3 import dbapi2 as sqlite

import pytest

from iatidataquality import app
from iatidq.sample_work import db as sample_db

# ─── helpers ────────────────────────────────────────────────────────────────


def _conn(path):
    return sqlite.connect(path)


def _insert_work_item(
    c, uuid, org_id, test_id, round_id, activity_id="act-1", xml_data="<iati-activity/>"
):
    c.execute(
        """
        insert into sample_work_item
            (uuid, organisation_id, test_id, activity_id, package_id,
             xml_data, xml_parent_data, test_kind, result, sampling_round_id)
        values (?,?,?,?,?,?,?,?,?,?)""",
        (
            uuid,
            org_id,
            test_id,
            activity_id,
            "pkg-1",
            xml_data,
            None,
            "simple",
            1,
            round_id,
        ),
    )


def _insert_response(c, uuid, response=1):
    c.execute(
        """
        insert into sample_result (uuid, response, comment, user_id, unsure)
        values (?, ?, ?, ?, ?)""",
        (uuid, response, "", 1, 0),
    )


# ─── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def sampling_db(tmp_path):
    """Temporary SQLite DB with fresh schema; sets SAMPLING_DB_FILENAME."""
    db_path = str(tmp_path / "sample_test.db")
    original = app.config.get("SAMPLING_DB_FILENAME")
    app.config["SAMPLING_DB_FILENAME"] = db_path

    conn = _conn(db_path)
    c = conn.cursor()
    sample_db.ensure_schema(c)
    conn.commit()
    conn.close()

    yield db_path

    app.config["SAMPLING_DB_FILENAME"] = original


# ─── ensure_schema ───────────────────────────────────────────────────────────


def test_ensure_schema_fresh_creates_all_tables(tmp_path):
    conn = _conn(str(tmp_path / "fresh.db"))
    c = conn.cursor()
    sample_db.ensure_schema(c)
    conn.commit()

    c.execute("select name from sqlite_master where type='table' order by name")
    tables = {r[0] for r in c.fetchall()}
    assert {"sample_work_item", "sample_result", "sampling_round"} == tables

    c.execute("select name from sqlite_master where type='view'")
    views = {r[0] for r in c.fetchall()}
    assert "sample_full" in views


def test_ensure_schema_legacy_migration(tmp_path):
    """A pre-sampling-round DB gets sampling_round table and column backfilled."""
    conn = _conn(str(tmp_path / "legacy.db"))
    c = conn.cursor()

    # Build old schema without sampling_round
    c.execute("""create table sample_work_item (
        uuid char(36) unique not null, organisation_id int not null,
        test_id int not null, activity_id varchar(100) not null,
        package_id varchar(100) not null, xml_data text not null,
        xml_parent_data text, test_kind varchar(20) not null,
        result NUMERIC not null)""")
    c.execute("""create table sample_result (
        uuid char(36) unique not null, response int not null,
        comment text not null, user_id int not null, unsure int not null)""")
    c.execute("""create view sample_full as
        select * from sample_work_item left join sample_result using (uuid)""")
    c.execute("""insert into sample_work_item
        (uuid, organisation_id, test_id, activity_id, package_id,
         xml_data, xml_parent_data, test_kind, result)
        values ('aaaa', 1, 1, 'act', 'pkg', '<x/>', null, 'simple', 1)""")
    conn.commit()

    sample_db.ensure_schema(c)
    conn.commit()

    c.execute("select id, name from sampling_round")
    rounds = c.fetchall()
    assert len(rounds) == 1
    assert rounds[0][1] == "Round 1"

    c.execute("select sampling_round_id from sample_work_item")
    round_ids = [r[0] for r in c.fetchall()]
    assert all(
        rid == rounds[0][0] for rid in round_ids
    ), "all legacy items should be assigned to Round 1"


def test_ensure_schema_idempotent(tmp_path):
    conn = _conn(str(tmp_path / "idempotent.db"))
    c = conn.cursor()
    sample_db.ensure_schema(c)
    conn.commit()
    sample_db.ensure_schema(c)
    conn.commit()

    c.execute("select count(*) from sampling_round")
    assert c.fetchone()[0] == 0  # no spurious rows inserted


# ─── create_round ────────────────────────────────────────────────────────────


def test_create_round_additive(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()

    r1 = sample_db.create_round(c, name="Round 1")
    conn.commit()
    r2 = sample_db.create_round(c, name="Round 2")
    conn.commit()

    assert r1 == 1
    assert r2 == 2

    c.execute("select id, name from sampling_round order by id")
    rows = c.fetchall()
    assert rows == [(1, "Round 1"), (2, "Round 2")]


def test_create_round_default_name(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    round_id = sample_db.create_round(c)
    conn.commit()

    c.execute("select name from sampling_round where id = ?", (round_id,))
    assert c.fetchone()[0] == "Round 1"


def test_create_round_replace_latest_cleans_items_and_responses(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()

    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "uuid-r1", 1, 1, r1)
    _insert_response(c, "uuid-r1")
    conn.commit()

    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "uuid-r2", 1, 1, r2)
    conn.commit()

    r2_new = sample_db.create_round(c, name="Round 2 redo", replace_latest=True)
    conn.commit()

    assert r2_new == r2  # reuses the same id

    c.execute("select name from sampling_round where id = ?", (r2,))
    assert c.fetchone()[0] == "Round 2 redo"

    # round 2's work item and response are gone
    c.execute("select uuid from sample_work_item where sampling_round_id = ?", (r2,))
    assert c.fetchall() == []

    # round 1's data is untouched
    c.execute("select uuid from sample_work_item where sampling_round_id = ?", (r1,))
    assert len(c.fetchall()) == 1
    c.execute("select uuid from sample_result")
    assert len(c.fetchall()) == 1


def test_create_round_replace_latest_raises_when_no_rounds(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    with pytest.raises(ValueError, match="No existing sampling round to replace"):
        sample_db.create_round(c, replace_latest=True)


# ─── latest_round_id / all_rounds ────────────────────────────────────────────


def test_latest_round_id_empty(sampling_db):
    assert sample_db.latest_round_id() is None


def test_latest_round_id_returns_max(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    sample_db.create_round(c)
    sample_db.create_round(c)
    conn.commit()

    assert sample_db.latest_round_id() == 2


def test_all_rounds_empty(sampling_db):
    assert sample_db.all_rounds() == []


def test_all_rounds_returns_ordered(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    sample_db.create_round(c, name="Alpha", snapshot_date="2026-01-01")
    sample_db.create_round(c, name="Beta", snapshot_date="2026-02-01")
    conn.commit()

    rounds = sample_db.all_rounds()
    assert len(rounds) == 2
    assert rounds[0]["name"] == "Alpha"
    assert rounds[0]["snapshot_date"] == "2026-01-01"
    assert rounds[1]["name"] == "Beta"
    assert rounds[1]["id"] == 2


# ─── all_sample_orgs / count_samples ─────────────────────────────────────────


def test_all_sample_orgs_no_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", org_id=10, test_id=1, round_id=r1)
    _insert_work_item(c, "u2", org_id=20, test_id=1, round_id=r2)
    conn.commit()

    org_ids = {r[0] for r in sample_db.all_sample_orgs()}
    assert org_ids == {10, 20}


def test_all_sample_orgs_round_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", org_id=10, test_id=1, round_id=r1)
    _insert_work_item(c, "u2", org_id=20, test_id=1, round_id=r2)
    conn.commit()

    assert {r[0] for r in sample_db.all_sample_orgs(round_id=r1)} == {10}
    assert {r[0] for r in sample_db.all_sample_orgs(round_id=r2)} == {20}


def test_count_samples_round_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", 1, 1, r1)
    _insert_work_item(c, "u2", 1, 1, r1)
    _insert_work_item(c, "u3", 1, 1, r2)
    conn.commit()

    assert sample_db.count_samples(round_id=r1) == 2
    assert sample_db.count_samples(round_id=r2) == 1
    assert sample_db.count_samples() == 3


def test_count_samples_org_and_test_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", org_id=1, test_id=1, round_id=r1)
    _insert_work_item(c, "u2", org_id=1, test_id=2, round_id=r1)
    _insert_work_item(c, "u3", org_id=2, test_id=1, round_id=r1)
    conn.commit()

    assert sample_db.count_samples(org_id=1, test_id=1) == 1
    assert sample_db.count_samples(org_id=1) == 2
    assert sample_db.count_samples(test_id=1) == 2


# ─── read_db_response ────────────────────────────────────────────────────────


def test_read_db_response_round_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "uuid-r1", 1, 1, r1)
    _insert_work_item(c, "uuid-r2", 1, 1, r2)
    conn.commit()

    r1_items = sample_db.read_db_response(round_id=r1)
    assert len(r1_items) == 1
    assert r1_items[0]["uuid"] == "uuid-r1"
    assert r1_items[0]["sampling_round_id"] == r1

    r2_items = sample_db.read_db_response(round_id=r2)
    assert len(r2_items) == 1
    assert r2_items[0]["uuid"] == "uuid-r2"


def test_read_db_response_org_and_test_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", org_id=1, test_id=10, round_id=r1)
    _insert_work_item(c, "u2", org_id=1, test_id=20, round_id=r1)
    _insert_work_item(c, "u3", org_id=2, test_id=10, round_id=r1)
    conn.commit()

    # org filter
    assert len(sample_db.read_db_response(org_id=1)) == 2
    # test filter (this was the pre-existing bug: previously ignored)
    assert len(sample_db.read_db_response(test_id=10)) == 2
    # combined
    items = sample_db.read_db_response(org_id=1, test_id=10)
    assert len(items) == 1
    assert items[0]["uuid"] == "u1"


def test_read_db_response_uuid_filter(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "11111111-1111-1111-1111-111111111111", 1, 1, r1)
    _insert_work_item(c, "22222222-2222-2222-2222-222222222222", 1, 1, r1)
    conn.commit()

    items = sample_db.read_db_response(uuid="11111111-1111-1111-1111-111111111111")
    assert len(items) == 1
    assert items[0]["uuid"] == "11111111-1111-1111-1111-111111111111"


def test_read_db_response_includes_response_data(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "uuid-resp", 1, 1, r1)
    _insert_response(c, "uuid-resp", response=1)
    conn.commit()

    items = sample_db.read_db_response(round_id=r1)
    assert items[0]["response"] == 1
    assert items[0]["user_id"] == 1


# ─── work_item_generator ─────────────────────────────────────────────────────


def test_work_item_generator_returns_unreviewed(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "reviewed", 1, 1, r1, activity_id="act-reviewed")
    _insert_response(c, "reviewed", response=1)
    _insert_work_item(c, "pending", 1, 1, r1, activity_id="act-pending")
    conn.commit()

    wi = sample_db.work_item_generator()
    assert wi["uuid"] == "pending"
    assert wi["sampling_round_id"] == r1


def test_work_item_generator_defaults_to_latest_round(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    # r1 has an unreviewed item, r2 also has one
    _insert_work_item(c, "r1-item", 1, 1, r1)
    _insert_work_item(c, "r2-item", 1, 1, r2)
    conn.commit()

    wi = sample_db.work_item_generator()
    assert wi["uuid"] == "r2-item"
    assert wi["sampling_round_id"] == r2


def test_work_item_generator_raises_when_round_exhausted(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "reviewed", 1, 1, r1)
    _insert_response(c, "reviewed", response=1)
    conn.commit()

    with pytest.raises(sample_db.NoMoreSamplingWork):
        sample_db.work_item_generator(round_id=r1)


def test_work_item_generator_raises_with_no_rounds(sampling_db):
    with pytest.raises(sample_db.NoMoreSamplingWork):
        sample_db.work_item_generator()


# ─── get_total_results ────────────────────────────────────────────────────────


def test_get_total_results_scoped_to_round(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()

    _insert_work_item(c, "r1a", 1, 1, r1)
    _insert_work_item(c, "r1b", 1, 1, r1)
    _insert_response(c, "r1a", response=1)
    _insert_response(c, "r1b", response=0)
    _insert_work_item(c, "r2a", 1, 1, r2)
    _insert_response(c, "r2a", response=1)
    conn.commit()

    r1_results = sample_db.get_total_results(round_id=r1)
    r1_by_response = {r["response"]: r["count"] for r in r1_results}
    assert r1_by_response[1] == 1
    assert r1_by_response[0] == 1

    r2_results = sample_db.get_total_results(round_id=r2)
    assert len(r2_results) == 1
    assert r2_results[0]["response"] == 1
    assert r2_results[0]["count"] == 1


def test_get_total_results_defaults_to_latest_round(sampling_db):
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "r1a", 1, 1, r1)
    _insert_response(c, "r1a", response=1)
    _insert_work_item(c, "r2a", 1, 1, r2)
    _insert_response(c, "r2a", response=0)
    conn.commit()

    results = sample_db.get_total_results()  # should default to r2
    assert len(results) == 1
    assert results[0]["response"] == 0


# ─── XML content belongs to the correct round ────────────────────────────────


def test_read_db_response_xml_from_correct_round(sampling_db):
    """XML content returned must belong to the queried round, not another round."""
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", 1, 1, r1, xml_data='<activity id="round1"/>')
    _insert_work_item(c, "u2", 1, 1, r2, xml_data='<activity id="round2"/>')
    conn.commit()

    r1_items = sample_db.read_db_response(round_id=r1)
    assert r1_items[0]["xml_data"] == '<activity id="round1"/>'

    r2_items = sample_db.read_db_response(round_id=r2)
    assert r2_items[0]["xml_data"] == '<activity id="round2"/>'


def test_work_item_generator_xml_from_correct_round(sampling_db):
    """work_item_generator must return the XML for the round it queried."""
    conn = _conn(sampling_db)
    c = conn.cursor()
    r1 = sample_db.create_round(c)
    r2 = sample_db.create_round(c)
    conn.commit()
    _insert_work_item(c, "u1", 1, 1, r1, xml_data='<activity id="round1"/>')
    _insert_work_item(c, "u2", 1, 1, r2, xml_data='<activity id="round2"/>')
    conn.commit()

    wi_r1 = sample_db.work_item_generator(round_id=r1)
    assert wi_r1["xml_data"] == '<activity id="round1"/>'

    wi_r2 = sample_db.work_item_generator(round_id=r2)
    assert wi_r2["xml_data"] == '<activity id="round2"/>'
