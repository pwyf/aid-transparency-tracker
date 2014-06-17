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

keys = ["uuid", "organisation_id", "test_id", "activity_id", "package_id",
        "xml_data", "xml_parent_data", "test_kind"]

keys_response = ["uuid", "organisation_id", "test_id", "activity_id",
    "package_id", "xml_data", "xml_parent_data", "test_kind", "response",
    "unsure"]

def default_filename():
    return config.DB_FILENAME

def make_db(filename, work_items):
    if os.path.exists(filename):
        os.unlink(filename)

    database = sqlite.connect(filename)
    c = database.cursor()

    stmts = [create_sql, create_sql2, create_sql_offered, create_sql3]

    [ c.execute(stmt) for stmt in stmts ]

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
                 from sample_work_item;""")

    for wi in c.fetchall():
        data = dict([ (keys[i], wi[i]) for i in range(0, 8) ])

        yield data

def read_db_response():
    filename = default_filename()

    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select sample_work_item.uuid as uuid,
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
                sample_work_item.uuid=sample_result.uuid;""")

    for wi in c.fetchall():
        data = dict([ (keys_response[i], wi[i]) for i in range(0, 10) ])
        yield data


def work_item_generator(f):
    filename = default_filename()

    for wi in read_db(filename):
        yield f(wi)

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

def save_offer(work_item_uuid):
    filename = default_filename()
    database = sqlite.connect(filename)
    c = database.cursor()

    try:
        c.execute('''insert into sample_offer ("uuid", "offered_time", "offered")
                       values (?, CURRENT_TIMESTAMP, ?);''', (work_item_uuid, 1))
    except sqlite3.IntegrityError:
        database.rollback()
        raise
    
    database.commit()
