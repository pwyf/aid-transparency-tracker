#!/usr/bin/env python

import sys
import psycopg2
import requests
import random

def save_url(url, filename):
    resp = requests.get(url)
    with file(filename, 'w') as f:
        f.write(resp.content)

def query(*args):
    db = psycopg2.connect(user='iatidq', database='iatidq')
    c = db.cursor()
    c.execute(*args)
    return c.fetchall()

class SampleOrgTest(object):
    def __init__(self, organisation_id, test_id):
        self.org_id = organisation_id
        self.test_id = test_id

    def qualifies(self):
        rows = query('''select result_data from result where organisation_id = %s and test_id = %s where result_data != 0''', [self.organisation_id, self.test_id])
        return len(rows) >= 1
        
    def activity_ids(self):
        rows = query('''select result_identifier from result where organisation_id = %s and test_id = %s where result_data != 0''', [self.organisation_id, self.test_id])
        ids = [ i[0] for i in rows ]
        return ids

    def sample_activity_ids(self):
        return random.choice(self.activity_ids())
