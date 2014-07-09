#!/usr/bin/env python

import sys
import psycopg2
from psycopg2.extensions import adapt
import requests
import random
import lxml.etree
import json
import os
import uuid
import sys
import re
import config

IATI_DIR = config.DATA_STORAGE_DIR

class NoIATIActivityFound(Exception):
    pass

def save_url(url, filename):
    resp = requests.get(url)
    with file(filename, 'w') as f:
        f.write(resp.content)

def query(*args):
    import config
    db_config = config.db_config
    db = psycopg2.connect(**db_config)
    c = db.cursor()
    c.execute(*args)
    return c.fetchall()


def organisation_ids():
    return query('select id from organisation;')

class WorkItems(object):
    def __init__(self, org_ids, test_ids):
        self.org_ids = org_ids
        self.test_ids = test_ids

    def test_string_of_test_id(self, test_id):
        results = query('''select name from test where id = %s;''', (test_id,));
        assert len(results) == 1
        return results[0][0]

    def kind_of_test(self, test_id):
        test_string = self.test_string_of_test_id(test_id)
        return self.kind_of_test_string(test_string)

    def kind_of_test_string(self, test_string):
        import test_mapping

        return test_mapping.test_to_kind[test_string]

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
                    try:
                        act = sot.xml_of_activity(act_id)
                        parent_act = sot.xml_of_parent_activity(act_id)
                    except NoIATIActivityFound:
                        continue

                    u = str(uuid.uuid4())

                    args = {
                        "uuid": u,
                        "organisation_id": org_id,
                        "test_id": test_id,
                        "activity_id": act_id[0],
                        "package_id": act_id[1],
                        "xml_data": act,
                        "xml_parent_data": parent_act,
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
                            and result_data = 1''', 
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
        if 0 == len(activities):
            raise NoIATIActivityFound
        # Some publishers are re-using iati identifiers, so unfortunately
        # we can't rely on this assertion.
        # At least we know we have >0 though.
        # assert len(activities) == 1
        return lxml.etree.tostring(activities[0], pretty_print=True)

    def xml_of_parent_activity(self, activity):
        activity_id, pkg = activity
        xml = self.xml_of_package(pkg)

        xpath_str = '//iati-activity[iati-identifier/text()="%s"]'
        activities = xml.xpath(xpath_str % activity_id)

        # More than one IATI activity could be found (if a publisher re-using
        # iati-identifiers, but should be >0.
        assert len(activities) > 0
        activity_xml = activities[0]

        xpath_str = '''related-activity[@type='1']/@ref'''
        related_activity_ids = activity_xml.xpath(xpath_str)
        
        count_relateds = len(related_activity_ids)
        if 0 == count_relateds:
            return None

        assert 0 < count_relateds

        xpath_str = '''//iati-activity[iati-identifier/text()="%s"]'''
        
        parent_id = related_activity_ids[0]
        
        try:
            return lxml.etree.tostring(xml.xpath(xpath_str % parent_id)[0])
        except IndexError:
            return None


class DocumentLink(object):
    def __init__(self, url, title, elt, codelists):
        self.elt = elt
        self.title = title
        self.url = url
        self.codelists = codelists

    def __repr__(self):
        return '''<DocumentLink: %s>''' % self.url

    def to_dict(self):
        def getCategory(category, codelists):
            return {"category": codelists[category],
                    "category_code": category }
        
        def getCategories(categories, codelists):
            return [ getCategory(category, codelists) for category in categories ]
    
        data = {
            "name": self.title,
            "url": self.url,
            "categories": getCategories(self.elt.xpath('category/@code'), 
                                       self.codelists)
            }
        return data

class DocumentLinks(object):
    def __init__(self, xml_string, codelists):
        root = lxml.etree.fromstring(xml_string)
        self.root = root
        self.codelists = codelists

    def get_links(self):
        for i in self.root.iterfind('document-link'):
            url = i.attrib["url"]
            title = i.xpath('title/text()')
            codelists = self.codelists
            yield DocumentLink(url, title, i, codelists)

class Location(object):
    def __init__(self, elt):
        self.elt = elt

    def __repr__(self):
        return '''<Location: %s>''' % self.elt

    def to_dict(self):
        data = {
            "name": self.elt.xpath('name/text()'),
            "description": self.elt.xpath('description/text()'),
            "longitude": self.elt.xpath('coordinates/@longitude'),
            "latitude": self.elt.xpath('coordinates/@latitude'),
            }
        return data   

class Locations(object):
    def __init__(self,xml_string):
        root = lxml.etree.fromstring(xml_string)
        self.root = root

    def get_locations(self):
        for i in self.root.iterfind('location'):
            yield Location(i)

class Period(object):
    def __init__(self, elt):
        self.elt = elt

    def to_dict(self):
        def format_pct(value):
            return '<div class="progress"><div class="bar" style="width: ' + str(round(value,2)) + '%;"></div></div>'

        def calc_pct(target, actual):
            if (target and actual):
                try:
                    target = re.sub(",", "", target[0])
                    target = re.sub("%", "", target)
                    actual = re.sub(",", "", actual[0])
                    actual = re.sub("%", "", actual)
                    return format_pct((float(actual) / float(target)) * 100.00)
                except Exception, e:
                    return ""

        data = {
            'start_date': self.elt.xpath('period-start/@iso-date'),
            'end_date': self.elt.xpath('period-end/@iso-date'),
            'target': self.elt.xpath('target/@value'),
            'actual': self.elt.xpath('actual/@value'),
            'pct': calc_pct(self.elt.xpath('target/@value'), 
                            self.elt.xpath('actual/@value'))
        }
        return data

class Indicator(object):
    def __init__(self,elt):
        self.elt = elt

    def elt_text_or_BLANK(self, key):
        elt = self.elt.find(key)
        return getattr(elt, "text", "")

    def to_dict(self):
        def get_period(period):
            return Period(period).to_dict()

        def get_periods(periods):
            return [ get_period(period)
                        for period in periods ]
        data = {
            "title": self.elt_text_or_BLANK("title"),
            "description": self.elt_text_or_BLANK("description"),
            "periods": get_periods(self.elt.xpath('period')),
        }
        return data

class Result(object):
    def __init__(self, elt):
        self.elt = elt

    def __repr__(self):
        return '''<Result: %s>''' % self.elt

    def elt_text_or_BLANK(self, key):
        elt = self.elt.find(key)
        return getattr(elt, "text", "")

    def to_dict(self):
        def get_indicator(indicator):
            return Indicator(indicator).to_dict()
        
        def get_indicators(indicators):
            return [ get_indicator(indicator) 
                        for indicator in indicators ]

        data = {
            "title": self.elt_text_or_BLANK("title"),
            "description": self.elt_text_or_BLANK("description"),
            "indicators": get_indicators(self.elt.xpath('indicator')),
            }
        return data

class Results(object):
    def __init__(self, xml_string):
        root = lxml.etree.fromstring(xml_string)
        self.root = root

    def get_results(self):
        for i in self.root.iterfind('result'):
            yield Result(i)

class Condition(object):
    def __init__(self, elt):
        self.elt = elt

    def __repr__(self):
        return '''<Condition: %s>''' % self.elt

    def to_dict(self):
        data = {
            "type": self.elt.xpath("@type"),
            "text": self.elt.text,
            }
        return data

class Conditions(object):
    def __init__(self, xml_string):
        root = lxml.etree.fromstring(xml_string)
        self.root = root

    def get_conditions(self):
        return { 'attached': self.root.xpath("conditions/@attached"),
                 'conditions': [ Condition(condition).to_dict()
                        for condition in self.root.xpath('conditions/condition') ] }

class ActivityInfo(object):
    def __init__(self, xml_string):
        self.root = lxml.etree.fromstring(xml_string)
        self.title = self.elt_text_or_MISSING("title")
        self.description = self.elt_text_or_MISSING("description")

    def elt_text_or_MISSING(self, key):
        elt = self.root.find(key)
        return getattr(elt, "text", "MISSING")

class NoMatchingTest(Exception):
    pass

class TestInfo(object):
    def __init__(self, test_foxpath):
        self.test_string = test_foxpath
        self.test_id = self.id_of_string()

    def id_of_string(self):
        sql = '''select id from test where name = %s;'''
        q = sql % adapt(self.test_string).getquoted()

        results = query(q)
        if len(results) < 1:
            raise NoMatchingTest(self.test_string)
        return results[0][0]
