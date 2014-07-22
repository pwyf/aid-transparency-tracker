create_sql = """
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
create_sql2 = """
    create table sample_result (
        uuid char(36) unique not null,
        response int not null,
        unsure int not null
    );
"""
create_sql_offered = """
    create table sample_offer (
        uuid char(36) unique not null,
        offered_time DATETIME not null,
        offered bool not null
    );
"""

create_sql3 = """
    create view sample_full as
        select * from sample_work_item 
            left join sample_result using (uuid)
            left join sample_offer using (uuid);
"""

from sqlite3 import dbapi2 as sqlite
import sqlite3
import os
import config
import logging
import json
from uuid import UUID

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
    stmts = [create_sql, create_sql2, create_sql_offered, create_sql3]

    [ c.execute(stmt) for stmt in stmts ]

def make_db(filename, work_items, create):
    if create:
        if os.path.exists(filename):
            os.unlink(filename)

    database = sqlite.connect(filename)
    c = database.cursor()

    if create:
        create_db(c)

    for wi in work_items:
        wi_info = tuple(map(lambda k: wi[k], keys))

        c.execute("""insert into sample_work_item 
                        ("uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", 
                         "xml_parent_data", "test_kind")
                        values (?,?,?,?,?,?,?,?);
                  """, wi_info)

    database.commit()


def read_db(filename):
    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select "uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", "xml_parent_data", 
                         "test_kind"
                 from sample_full 
                 where response is null 
                   and (offered != 1
                   or offered is null)
                 limit 1;""")

    wis = c.fetchall()
    if 0 == len(wis):
        raise NoMoreSamplingWork

    # ignore the case where limit 1 nevertheless returns >1 result

    wi = wis[0]
    data = dict([ (keys[i], wi[i]) for i in range(0, 8) ])

    work_item_uuid = wi[0] # hack
    try:
        save_offer(database, work_item_uuid)
        database.commit()
        return data
    except:
        logging.error("error saving UUID: %s" % work_item_uuid)
        database.rollback()
        raise

def read_db_response(uuid=None):
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
                sample_work_item.uuid=sample_result.uuid %s;"""

    if uuid:
        # Ensure uuid var is really a uuid
        UUID(uuid)
        whereclause = """
                where sample_work_item.uuid="%s" """ % uuid
    else:
        whereclause = ""

    stmt = query % (whereclause,)

    c.execute(stmt)

    for wi in c.fetchall():
        data = dict([ (keys_response[i], wi[i]) for i in range(0, 10) ])
        yield data

def work_item_generator(f):
    filename = default_filename()

    wi = read_db(filename)
    return f(wi)

def save_response(work_item_uuid, response, unsure=False):
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    try:
        c.execute('''insert into sample_result ("uuid", "response", "unsure")
                       values (?, ?, ?);''', (work_item_uuid, response, unsure))
    except sqlite3.IntegrityError:
        database.rollback()
        raise
    
    database.commit()

def update_response(work_item_uuid, response, unsure=False):
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    result = c.execute('''update sample_result set response=?, unsure=?
                       where uuid=?;''', (response, unsure, work_item_uuid))
   
    try:
        assert result.rowcount > 0
    except AssertionError:
        database.rollback()
        raise

    database.commit()

def save_offer(database, work_item_uuid):
    c = database.cursor()

    c.execute('''insert into sample_offer ("uuid", "offered_time", "offered")
                   values (?, CURRENT_TIMESTAMP, ?);''', (work_item_uuid, True))

def flush_offered_work():
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute('''select uuid from sample_full
                   where offered = 1 and response is null;''')

    uuids = [ row[0] for row in c.fetchall() ]

    for uuid in uuids:
        c.execute('''delete from sample_offer where uuid = ?;''', (uuid,))

    db.commit()
    
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
    join sample_result on sample_result.uuid=sample_work_item.uuid
    group by organisation_id, 
             test_id,
             sample_result.response;
    """)
    
    out = []
    for wi in c.fetchall():
        data = dict([ (total_results_response[i], wi[i]) for i in range(0, 4) ])
        out.append(data)
    return out

def get_summary_org_test(results):
    from iatidq import dqorganisations, dqtests
    orgtests = set(map(lambda x: (x['organisation_id'], x['test_id']), results))
    ot = []

    for orgtest in orgtests:
        orgtest_results = filter(lambda x: (
                x['organisation_id'] == orgtest[0] and 
                x['test_id'] == orgtest[1]
                ), results)

        success = filter(lambda x: x['response'] == 1, orgtest_results)
        fail    = filter(lambda x: x['response'] != 1, orgtest_results)
        
        totalsuccess = sum(map(lambda x: x['count'], success))
        totalfail    = sum(map(lambda x: x['count'], fail))
        
        pct = float(totalsuccess) / (totalsuccess + totalfail) * 100

        passfail = pct >= 50.0

        if passfail:
            passfail_class='success'
            passfail_text='PASS'
        else:
            passfail_class='important'
            passfail_text='FAIL'
        
        ot.append({ 'organisation_id': orgtest[0],
                    'organisation': dqorganisations.organisation_by_id(orgtest[0]),
                    'test_id': orgtest[1],
                    'test': dqtests.tests(orgtest[1]),
                    'success': round(pct, 2),
                    'total': totalsuccess+totalfail,
                    'results': orgtest_results,
                    'pass': passfail,
                    'passfail_text': passfail_text,
                    'passfail_class': passfail_class,
                    })
    return ot

def get_passed_failed(ot, ok=True):
    return filter(lambda x: x['pass'] == ok, ot)

def passes_failures(passes=True):
    results = get_total_results()
    ot = get_summary_org_test(results)
    pf = get_passed_failed(ot, passes)
    return map(lambda x: ({
                'organisation_id': x['organisation_id'], 
                'test_id': x['test_id']
                }), pf)

def get_passes_from_db():
    with open('passes.json', 'w') as outfile:
        json.dump(passes_failures(), outfile)

def get_fails_from_db():
    with open('fails.json', 'w') as outfile:
        json.dump(passes_failures(False), outfile)

def get_uuid_by_org_test(org, test):
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()
    
    c.execute("""
    select sample_work_item.uuid
    from sample_work_item
    where organisation_id=%s
    and test_id=%s
    """ % (org, test))
    
    return c.fetchall()

def update_db_for_passes():
    with open('passes.json', 'r') as readfile:
        data = json.load(readfile)
        for ot in data:
            work_item_uuids = get_uuid_by_org_test(ot['organisation_id'], 
                                                   ot['test_id'])
            for uuid in work_item_uuids:
                save_response(uuid[0], 1)
