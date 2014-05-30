#!/usr/bin/env python

import sys
import psycopg2
import requests
import random
import lxml.etree

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
        ROOT= '/var/tmp/iati'
        return lxml.etree.parse(ROOT + '/' + package_name + '.xml')

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


class DocumentLinks(object):
    def __init__(self, xml_string):
        root = lxml.etree.fromstring(xml_string)

        self.root = root

    def get_links(self):
        for i in self.root.iterfind('document-link'):
            url = i.attrib["url"]
            title = i.find('title').text

            yield DocumentLink(url, title, i)
