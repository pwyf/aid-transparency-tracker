create_sql = """
    create table sample_work_item (
        uuid char(36) unique not null,
        organisation_id int not null,
        test_id int not null,
        activity_id varchar(100) not null,
        package_id varchar(100) not null,
        xml_data text not null,
        test_kind varchar(20)
    );
"""
create_sql2 = """
    create table sample_result (
        uuid char(36) unique not null,
        response int not null
    );
"""

from sqlite3 import dbapi2 as sqlite
import os

keys = ["uuid", "organisation_id", "test_id", "activity_id", "package_id",
        "xml_data", "test_kind"]

keys_response = ["uuid", "organisation_id", "test_id", "activity_id", "package_id",
        "xml_data", "test_kind", "response"]

def make_db(filename, work_items):
    if os.path.exists(filename):
        os.unlink(filename)

    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute(create_sql)
    c.execute(create_sql2)

    for wi in work_items:
        wi_info = tuple(map(lambda k: wi[k], keys))

        c.execute("""insert into sample_work_item 
                        ("uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", "test_kind")
                        values (?,?,?,?,?,?,?);
                  """, wi_info)

    database.commit()


def read_db(filename):
    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select "uuid", "organisation_id", "test_id", "activity_id",
                         "package_id", "xml_data", "test_kind"
                 from sample_work_item;""")

    for wi in c.fetchall():
        data = dict([ (keys[i], wi[i]) for i in range(0, 7) ])

        yield data

def read_db_response(filename):
    database = sqlite.connect(filename)
    c = database.cursor()

    c.execute("""select sample_work_item.uuid as uuid,
                sample_work_item.organisation_id as organisation_id, 
                sample_work_item.test_id as test_id,
                sample_work_item.activity_id as activity_id,
                sample_work_item.package_id as package_id, 
                sample_work_item.xml_data as xml_data, 
                sample_work_item.test_kind as test_kind,
                sample_result.response as response
                from sample_work_item
                left join sample_result on
                sample_work_item.uuid=sample_result.uuid;""")

    for wi in c.fetchall():
        data = dict([ (keys_response[i], wi[i]) for i in range(0, 8) ])
        yield data

def work_item_generator():
    filename = os.path.join(os.path.dirname(__file__), 
                            '../sample_work.db')
    for wi in sample_db.read_db(filename):
        yield make_sample_json(wi)

def save_response(work_item_uuid, response):
    filename = os.path.join(os.path.dirname(__file__), 
                                '../sample_work.db')

    database = sqlite.connect(filename)
    c = database.cursor()
        
    c.execute('''insert into sample_result ("uuid", "response")
                       values (?, ?);''', (work_item_uuid, response))
    database.commit()
