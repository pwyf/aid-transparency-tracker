import logging
import os
from uuid import UUID

from sqlite3 import IntegrityError, OperationalError, dbapi2 as sqlite

from iatidataquality import app


class NoMoreSamplingWork(Exception):
    pass


keys = ["uuid", "organisation_id", "test_id", "activity_id", "package_id",
        "xml_data", "xml_parent_data", "test_kind", "result", "sampling_round_id"]

keys_response = ["uuid", "organisation_id", "test_id", "activity_id",
                 "package_id", "xml_data", "xml_parent_data", "test_kind", "result",
                 "sampling_round_id",
                 "response", "comment", "user_id", "unsure"]

total_results_response = ["organisation_id", "test_id", "response", "count"]


def create_db(c):
    stmt = """
        create table sampling_round (
            id integer primary key,
            name text not null,
            snapshot_date text,
            created_at timestamp not null default current_timestamp
        );
    """
    c.execute(stmt)

    stmt = """
        create table sample_work_item (
            uuid char(36) unique not null,
            organisation_id int not null,
            test_id int not null,
            activity_id varchar(100) not null,
            package_id varchar(100) not null,
            xml_data text not null,
            xml_parent_data text,
            test_kind varchar(20) not null,
            result NUMERIC not null,
            sampling_round_id integer not null references sampling_round(id)
        );
    """
    c.execute(stmt)

    stmt = """
        create table sample_result (
            uuid char(36) unique not null,
            response int not null,
            comment text not null,
            user_id int not null,
            unsure int not null
        );
    """
    c.execute(stmt)

    stmt = """
        create view sample_full as
            select * from sample_work_item
                left join sample_result using (uuid);
    """
    c.execute(stmt)


def ensure_schema(c):
    """Create the sampling database schema if it doesn't exist yet, or
    migrate a legacy (pre-sampling-round) database in place."""
    c.execute("""select name from sqlite_master
                  where type='table' and name='sample_work_item';""")
    if not c.fetchall():
        create_db(c)
        return

    c.execute("""select name from sqlite_master
                  where type='table' and name='sampling_round';""")
    if c.fetchall():
        return

    # Legacy database: add the sampling_round table and column, and put
    # all existing sample work items into "Round 1".
    c.execute("""
        create table sampling_round (
            id integer primary key,
            name text not null,
            snapshot_date text,
            created_at timestamp not null default current_timestamp
        );
    """)
    c.execute("""alter table sample_work_item
                  add column sampling_round_id integer;""")
    c.execute("""insert into sampling_round (name, snapshot_date)
                  values ('Round 1', NULL);""")
    round1_id = c.lastrowid
    c.execute("""update sample_work_item set sampling_round_id = ?
                  where sampling_round_id is null;""", (round1_id,))


def latest_round_id():
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute('select max(id) from sampling_round;')
    return c.fetchone()[0]


def all_rounds():
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select id, name, snapshot_date, created_at
                  from sampling_round order by id;""")
    keys_round = ["id", "name", "snapshot_date", "created_at"]
    return [dict(list(zip(keys_round, row))) for row in c.fetchall()]


def create_round(c, name=None, snapshot_date=None, replace_latest=False):
    c.execute('select max(id) from sampling_round;')
    current_latest = c.fetchone()[0]

    if replace_latest:
        if current_latest is None:
            raise ValueError("No existing sampling round to replace")

        c.execute("""select uuid from sample_work_item
                      where sampling_round_id = ?;""", (current_latest,))
        uuids = [row[0] for row in c.fetchall()]
        if uuids:
            placeholders = ",".join("?" * len(uuids))
            c.execute("""delete from sample_result
                          where uuid in ({});""".format(placeholders), uuids)
        c.execute("""delete from sample_work_item
                      where sampling_round_id = ?;""", (current_latest,))
        c.execute('delete from sampling_round where id = ?;', (current_latest,))

        round_id = current_latest
        name = name or "Round {}".format(round_id)
        c.execute("""insert into sampling_round (id, name, snapshot_date)
                      values (?, ?, ?);""", (round_id, name, snapshot_date))
        return round_id

    round_id = (current_latest or 0) + 1
    name = name or "Round {}".format(round_id)
    c.execute("""insert into sampling_round (id, name, snapshot_date)
                  values (?, ?, ?);""", (round_id, name, snapshot_date))
    return round_id


def make_db(filename, orgs, tests, snapshot_path, round_name=None, replace_latest=False):
    from .sample_work import WorkItems

    database = sqlite.connect(filename)
    c = database.cursor()

    ensure_schema(c)
    database.commit()

    round_id = create_round(c, name=round_name, snapshot_date=snapshot_path,
                             replace_latest=replace_latest)
    database.commit()

    # populate db
    work_item_keys = keys[:-1]  # exclude sampling_round_id, set separately
    work_items = WorkItems(orgs, tests, snapshot_path)
    for wi in work_items:
        wi_info = tuple([wi[k] for k in work_item_keys]) + (round_id,)

        c.execute("""insert into sample_work_item
                        ("uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data",
                         "xml_parent_data", "test_kind", "result",
                         "sampling_round_id")
                        values (?,?,?,?,?,?,?,?,?,?);
                  """, wi_info)

        database.commit()

    return round_id


def all_sample_orgs(round_id=None):
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    query = 'select distinct organisation_id from sample_full'
    if round_id is not None:
        query += ' where sampling_round_id = "{}"'.format(round_id)
    c.execute(query)
    return c.fetchall()


def count_samples(org_id=None, test_id=None, round_id=None):
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    query = 'select count(*) from sample_full'

    where_arr = []
    if org_id:
        where_arr.append('organisation_id = "{}"'.format(org_id))
    if test_id:
        where_arr.append('test_id = "{}"'.format(test_id))
    if round_id is not None:
        where_arr.append('sampling_round_id = "{}"'.format(round_id))
    if where_arr:
        query += ' where '
        query += ' and '.join(where_arr)

    c.execute(query)
    return c.fetchone()[0]


def read_db_response(uuid=None, org_id=None, test_id=None, round_id=None, offset=0, limit=-1):
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    query = """select * from sample_full
                {where_clause}
                limit {limit} offset {offset}"""

    where_arr = []
    if uuid:
        # Ensure uuid var is really a uuid
        UUID(uuid)
        where_arr.append('uuid="{}"'.format(uuid))
    if org_id:
        where_arr.append('organisation_id="{}"'.format(org_id))
    if test_id:
        where_arr.append('test_id="{}"'.format(test_id))
    if round_id is not None:
        where_arr.append('sampling_round_id="{}"'.format(round_id))

    whereclause = ' where ' + ' and '.join(where_arr) if where_arr else ""

    stmt = query.format(
        where_clause=whereclause,
        limit=limit,
        offset=offset,
    )

    c.execute(stmt)

    return [dict(list(zip(keys_response, wi))) for wi in c.fetchall()]


def work_item_generator(round_id=None):
    filename = app.config['SAMPLING_DB_FILENAME']

    database = sqlite.connect(filename)
    c = database.cursor()

    if round_id is None:
        round_id = latest_round_id()
    if round_id is None:
        raise NoMoreSamplingWork

    c.execute("""select "uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", "xml_parent_data",
                         "test_kind", "result", "sampling_round_id"
                 from sample_full
                 where response is null
                 and sampling_round_id = ?
                 limit 1;""", (round_id,))

    wis = c.fetchall()
    if 0 == len(wis):
        raise NoMoreSamplingWork

    # ignore the case where limit 1 nevertheless returns >1 result

    wi = wis[0]
    data = dict(list(zip(keys, wi)))

    work_item_uuid = wi[0]  # hack
    try:
        database.commit()
        return data
    except:
        logging.error("error saving UUID: %s" % work_item_uuid)
        database.rollback()
        raise


def save_response(work_item_uuid, response, comment, user_id, unsure=False):
    filename = app.config['SAMPLING_DB_FILENAME']
    database = sqlite.connect(filename)
    c = database.cursor()

    result = c.execute('''update sample_result
                          set response=?, unsure=?, comment=?, user_id=?
                          where uuid=?;''',
                       (response, unsure, comment, user_id, work_item_uuid))

    if result.rowcount > 0:
        database.commit()
        return "update"

    try:
        c.execute('''insert into sample_result
                     ("uuid", "response", "unsure", "comment", "user_id")
                     values (?, ?, ?, ?, ?);''',
                  (work_item_uuid, response, unsure, comment, user_id))
    except IntegrityError:
        database.rollback()
        raise

    database.commit()
    return "create"


def get_total_results(round_id=None):

    filename = app.config['SAMPLING_DB_FILENAME']
    database = sqlite.connect(filename)
    c = database.cursor()

    if round_id is None:
        round_id = latest_round_id()

    c.execute("""
    select organisation_id,
           test_id,
           response,
           count(uuid) as count
    from sample_full
    where sampling_round_id = ?
    group by organisation_id,
             test_id,
             response;
    """, (round_id,))

    out = []
    for wi in c.fetchall():
        data = dict(list(zip(total_results_response, wi)))
        out.append(data)
    return out


def get_summary_org_test(results):
    from iatidq import models, dqtests

    orgtests = set([(x['organisation_id'], x['test_id']) for x in results])
    ot = []

    for orgtest in orgtests:
        orgtest_results = [x for x in results if (
                x['organisation_id'] == orgtest[0] and
                x['test_id'] == orgtest[1]
                )]

        success = [x for x in orgtest_results if x['response'] == 1]
        fail = [x for x in orgtest_results if x['response'] != 1 and x['response'] is not None]

        total = sum([x['count'] for x in orgtest_results])
        totalsuccess = sum([x['count'] for x in success])
        totalfail = sum([x['count'] for x in fail])

        if totalsuccess >= 10:
            pass_status = 'passing'
        elif totalfail > 10:
            pass_status = 'failing'
        else:
            pass_status = 'undecided'

        ot.append({
            'organisation_id': orgtest[0],
            'organisation': models.Organisation.find_or_fail(orgtest[0]),
            'test_id': orgtest[1],
            'test': dqtests.tests(orgtest[1]),
            'results': orgtest_results,
            'total': total,
            'total_pass': totalsuccess,
            'total_fail': totalfail,
            'pass_status': pass_status,
        })
    return ot
