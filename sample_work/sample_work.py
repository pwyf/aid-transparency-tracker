#!/usr/bin/env python

import sys
import psycopg2
import requests
import random
import lxml.etree
import json
import os
import uuid


# FIXME: should be in config (sort of)
IATI_DIR = '/var/tmp/iati'

def save_url(url, filename):
    resp = requests.get(url)
    with file(filename, 'w') as f:
        f.write(resp.content)

def query(*args):
    db = psycopg2.connect(user='iatidq', database='iatidq')
    c = db.cursor()
    c.execute(*args)
    return c.fetchall()


class WorkItems(object):
    def __init__(self, org_ids, test_ids):
        self.org_ids = org_ids
        self.test_ids = test_ids

        
    def kind_of_test(self, test_id):
        return "document"

    def __iter__(self):
        for org_id in self.org_ids:
            for test_id in self.test_ids:
                sot = SampleOrgTest(org_id, test_id)
                if not sot.qualifies():
                    continue
                act_ids = sot.activity_ids()
                sample_ids = sot.sample_activity_ids(10)

                test_kind = self.kind_of_test(test_id)

                for act_id in sample_ids:
                    act = sot.xml_of_activity(act_id)
                
                    u = str(uuid.uuid4())

                    args = {
                        "uuid": u,
                        "organisation_id": org_id,
                        "test_id": test_id,
                        "activity_id": act_id[0],
                        "package_id": act_id[1],
                        "xml_data": act,
                        "test_kind": test_kind
                        }
                    
                    yield args


class SampleOrgTest(object):
    def __init__(self, organisation_id, test_id):
        self.org_id = organisation_id
        self.test_id = test_id

        if self.qualifies():
            self.activities = self.activity_ids()
        else:
            self.activities = []

    def qualifies(self):
        rows = query('''select result_data from result 
                          where organisation_id = %s 
                            and test_id = %s 
                            and result_data != 0''', 
                     [self.org_id, self.test_id])
        return len(rows) >= 1
        
    def activity_ids(self):
        rows = query('''select result_identifier, package_name from result
                          left join package on result.package_id = package.id
                          where organisation_id = %s 
                            and test_id = %s 
                            and result_data != 0''', 
                     [self.org_id, self.test_id])
        ids = [ i for i in rows ]
        return ids

    def sample_activity_ids(self, max):
        act_ids = [i for i in self.activities]
        random.shuffle(act_ids)
        return act_ids[:max]

    def xml_of_package(self, package_name):
        filename = package_name + '.xml'
        path = os.path.join(IATI_DIR, filename)
        return lxml.etree.parse(path)

    def xml_of_activity(self, activity):
        activity_id, pkg = activity
        xml = self.xml_of_package(pkg)

        xpath_str = '//iati-activity[iati-identifier/text()="%s"]'

        activities = xml.xpath(xpath_str % activity_id)
        assert len(activities) == 1
        return lxml.etree.tostring(activities[0], pretty_print=True)


class DocumentLink(object):
    def __init__(self, url, title, elt):
        self.elt = elt
        self.title = title
        self.url = url

    def __repr__(self):
        return '''<DocumentLink: %s>''' % self.url

    def to_dict(self):
        data = {
            "name": self.title,
            "url": self.url,
            "categories": ["FIXME", "FIXMETOO"]
            }
        return data
    

class DocumentLinks(object):
    def __init__(self, xml_string):
        root = lxml.etree.fromstring(xml_string)

        self.root = root

    def get_links(self):
        for i in self.root.iterfind('document-link'):
            url = i.attrib["url"]
            title = i.find('title').text

            yield DocumentLink(url, title, i)

class ActivityInfo(object):
    def __init__(self, xml_string):
        self.root = lxml.etree.fromstring(xml_string)
        self.title = self.elt_text_or_MISSING("title")
        self.description = self.elt_text_or_MISSING("description")

    def elt_text_or_MISSING(self, key):
        elt = self.root.find(key)
        return getattr(elt, "text", "MISSING")

