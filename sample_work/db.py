import logging
import os
from uuid import UUID

from sqlite3 import dbapi2 as sqlite
import sqlite3

import config


class NoMoreSamplingWork(Exception): pass


keys = ["uuid", "organisation_id", "test_id", "activity_id", "package_id",
        "xml_data", "xml_parent_data", "test_kind"]

keys_response = ["uuid", "organisation_id", "test_id", "activity_id",
    "package_id", "xml_data", "xml_parent_data", "test_kind", "response",
    "unsure"]

total_results_response = ["organisation_id", "test_id", "response", "count"]


def default_filename():
    return config.DB_FILENAME


def create_db(c):
    stmt = """
        create table sample_work_item (
            uuid char(36) unique not null,
            organisation_id int not null,
            test_id int not null,
            activity_id varchar(100) not null,
            package_id varchar(100) not null,
            xml_data text not null,
            xml_parent_data text,
            test_kind varchar(20) not null
        );
    """
    c.execute(stmt)

    stmt = """
        create table sample_result (
            uuid char(36) unique not null,
            response int not null,
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


def make_db(filename, org_ids, test_ids, create):
    from sample_work import WorkItems

    if create:
        if os.path.exists(filename):
            print('Deleting old sampling db ...')
            os.unlink(filename)

    database = sqlite.connect(filename)
    c = database.cursor()

    if create:
        create_db(c)

    # populate db
    work_items = WorkItems(org_ids, test_ids, create)
    for wi in work_items:
        wi_info = tuple(map(lambda k: wi[k], keys))

        c.execute("""insert into sample_work_item
                        ("uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data",
                         "xml_parent_data", "test_kind")
                        values (?,?,?,?,?,?,?,?);
                  """, wi_info)

    database.commit()
    work_items.cleanup()


def count_all_samples():
    filename = default_filename()

    database = sqlite.connect(filename)
    c = database.cursor()

    query = """select count(*) from sample_work_item"""
    c.execute(query)
    return c.fetchone()[0]


def read_db_response(uuid=None, offset=0, limit=-1):
    filename = default_filename()

    database = sqlite.connect(filename)
    c = database.cursor()

    # this can all be replaced with a select against sample_full
    query = """select sample_work_item.uuid as uuid,
                sample_work_item.organisation_id as organisation_id,
                sample_work_item.test_id as test_id,
                sample_work_item.activity_id as activity_id,
                sample_work_item.package_id as package_id,
                sample_work_item.xml_data as xml_data,
                sample_work_item.xml_parent_data as xml_parent_data,
                sample_work_item.test_kind as test_kind,
                sample_result.response as response,
                sample_result.unsure as unsure
                from sample_work_item
                left join sample_result on
                sample_work_item.uuid=sample_result.uuid {where_clause}
                limit {limit} offset {offset}"""

    if uuid:
        # Ensure uuid var is really a uuid
        UUID(uuid)
        whereclause = 'where sample_work_item.uuid="{}"'.format(uuid)
    else:
        whereclause = ""

    stmt = query.format(
        where_clause=whereclause,
        limit=limit,
        offset=offset,
    )

    c.execute(stmt)

    return [dict(zip(keys_response, wi)) for wi in c.fetchall()]


def work_item_generator():
    filename = default_filename()

    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select "uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", "xml_parent_data",
                         "test_kind"
                 from sample_full
                 where response is null
                 limit 1;""")

    wis = c.fetchall()
    if 0 == len(wis):
        raise NoMoreSamplingWork

    # ignore the case where limit 1 nevertheless returns >1 result

    wi = wis[0]
    data = dict(zip(keys, wi))

    work_item_uuid = wi[0]  # hack
    try:
        database.commit()
        return data
    except:
        logging.error("error saving UUID: %s" % work_item_uuid)
        database.rollback()
        raise


def save_response(work_item_uuid, response, unsure=False):
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    result = c.execute('''update sample_result set response=?, unsure=?
                       where uuid=?;''', (response, unsure, work_item_uuid))

    if result.rowcount > 0:
        database.commit()
        return "update"

    try:
        c.execute('''insert into sample_result ("uuid", "response", "unsure")
                       values (?, ?, ?);''', (work_item_uuid, response, unsure))
    except sqlite3.IntegrityError:
        database.rollback()
        raise

    database.commit()
    return "create"

def get_total_results():

    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""
    select sample_work_item.organisation_id,
           sample_work_item.test_id,
           sample_result.response,
           count(sample_work_item.uuid) as count
    from sample_work_item
    left join sample_result on sample_result.uuid=sample_work_item.uuid
    group by organisation_id,
             test_id,
             sample_result.response;
    """)

    out = []
    for wi in c.fetchall():
        data = dict(zip(total_results_response, wi))
        out.append(data)
    return out

def get_summary_org_test(results):
    from iatidq import models, dqtests

    orgtests = set(map(lambda x: (x['organisation_id'], x['test_id']), results))
    ot = []

    for orgtest in orgtests:
        orgtest_results = filter(lambda x: (
                x['organisation_id'] == orgtest[0] and
                x['test_id'] == orgtest[1]
                ), results)

        success = filter(lambda x: x['response'] == 1, orgtest_results)
        fail = filter(lambda x: x['response'] != 1 and x['response'] is not None, orgtest_results)

        total = sum(map(lambda x: x['count'], orgtest_results))
        totalsuccess = sum(map(lambda x: x['count'], success))
        totalfail = sum(map(lambda x: x['count'], fail))

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
