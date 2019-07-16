#!/usr/bin/env python

import csv
import os
import random
import re
import uuid

import psycopg2
from psycopg2.extensions import adapt
import requests
import lxml.etree

from iatidq.models import AggregateResult, Test
from iatidataquality import app
from iatidq import models
from test_mapping import test_to_kind
import db
from beta.utils import slugify


def all_tests():
    all_tests = models.Test.all()
    sampling_tests = filter(lambda x: x.description in test_to_kind, all_tests)
    return sorted(sampling_tests, key=lambda x: x.description)


def all_orgs():
    all_orgs = models.Organisation.all()
    sample_org_ids = [x[0] for x in db.all_sample_orgs()]
    sample_orgs = filter(lambda x: x.id in sample_org_ids, all_orgs)
    return sorted(sample_orgs, key=lambda x: x.organisation_name)


def save_url(url, filename):
    resp = requests.get(url)
    with open(filename, 'w') as f:
        f.write(resp.content)


def query(*args, **kwargs):
    db_config = app.config['DATABASE_INFO']
    db = psycopg2.connect(**db_config)
    c = db.cursor()
    c.execute(*args)
    if kwargs.get("write"):
        db.commit()
    else:
        return c.fetchall()


class WorkItems(object):
    def __init__(self, orgs, tests, snapshot_date):
        self.orgs = orgs
        self.tests = tests
        self.snapshot_date = snapshot_date

    def test_desc_of_test_id(self, test_id):
        results = query('''select description from test where id = %s;''', (test_id,));
        assert len(results) == 1
        return results[0][0]

    def kind_of_test(self, test_id):
        test_desc = self.test_desc_of_test_id(test_id)
        return test_to_kind[test_desc]

    def __iter__(self):
        total_samples_todo = 20
        for org in self.orgs:
            print("Org: {}".format(org.organisation_name))
            for test in self.tests:
                print("Test: {}".format(test.description))

                sot = SampleOrgTest(org, test, self.snapshot_date)
                samples = sot.sample_activity_ids(total_samples_todo)

                test_kind = self.kind_of_test(test.id)

                for package_name, index, activity_id in samples:
                    act = sot.get_activity(package_name, index)
                    act_xml = (
                        lxml.etree.tostring(act, pretty_print=True)
                        if act is not None else None)
                    parent_act = sot.get_parent_activity(act, package_name)
                    parent_xml = (
                        lxml.etree.tostring(parent_act, pretty_print=True)
                        if parent_act is not None else None)

                    u = str(uuid.uuid4())

                    args = {
                        "uuid": u,
                        "organisation_id": org.id,
                        "test_id": test.id,
                        "activity_id": activity_id,
                        "package_id": package_name,
                        "xml_data": act_xml,
                        "xml_parent_data": parent_xml,
                        "test_kind": test_kind
                    }

                    yield args


class SampleOrgTest(object):
    def __init__(self, organisation, test, snapshot_date):
        self.organisation = organisation
        self.test = test
        self.snapshot_date = snapshot_date

    def sample_activity_ids(self, num_samples):
        ag_results = AggregateResult.where(
            test_id=self.test.id,
            organisation_id=self.organisation.id,
            aggregateresulttype_id=2,
        )
        total = int(sum([x.results_data / 100. * x.results_num
                         for x in ag_results]))
        if total <= num_samples:
            indexes = range(total)
        else:
            indexes = sorted(random.sample(range(total), num_samples))

        current_data_path = os.path.join(
            app.config.get('IATI_RESULT_PATH'),
            self.snapshot_date,
            self.organisation.registry_slug,
            'current_data.csv')
        test_path = os.path.join(
            app.config.get('IATI_RESULT_PATH'),
            self.snapshot_date,
            self.organisation.registry_slug,
            '{}.csv'.format(slugify(self.test.description)))
        with open(current_data_path) as cd_handler:
            with open(test_path) as test_handler:
                cd_reader = csv.DictReader(cd_handler)
                test_reader = csv.DictReader(test_handler)
                idx = 0
                for cd_result in cd_reader:
                    if indexes == []:
                        break
                    test_result = next(test_reader)
                    if cd_result['result'] == 'pass' and test_result['result'] == 'pass':
                        if idx == indexes[0]:
                            indexes.pop(0)
                            yield (
                                cd_result['dataset'],
                                int(cd_result['index']),
                                cd_result['identifier'],
                            )
                        idx += 1

    def xml_of_package(self, package_name):
        filename = package_name + '.xml'
        path = os.path.join(
            app.config['IATI_DATA_PATH'],
            self.snapshot_date,
            'data',
            self.organisation.registry_slug,
            filename)
        return lxml.etree.parse(path)

    def get_activity(self, package_name, index):
        xml = self.xml_of_package(package_name)

        activities = xml.xpath('//iati-activity[{}]'.format(index + 1))
        assert len(activities) > 0
        return activities[0]

    def get_parent_activity(self, activity, package_name):
        xml = self.xml_of_package(package_name)

        xpath_str = 'related-activity[@type="1"]/@ref'
        related_activity_ids = activity.xpath(xpath_str)

        if related_activity_ids == []:
            return None

        parent_id = related_activity_ids[0]

        xpath_str = '//iati-activity[iati-identifier/text()="{}"]'
        parent_acts = xml.xpath(xpath_str.format(parent_id))

        if parent_acts == []:
            return None

        return parent_acts[0]


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
            return {"category": codelists.get(category, 'ERROR'),
                    "category_code": category}

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

    def get_elt_text(self, elt, key):
        # IATI 2.01
        res = elt.xpath(key + '/narrative/text()')
        if not res:
            # IATI 1.05
            res = elt.xpath(key + '/text()')
        return res

    def get_links(self):
        for i in self.root.iterfind('document-link'):
            url = i.attrib.get("url")
            title = self.get_elt_text(i, 'title')
            codelists = self.codelists
            yield DocumentLink(url, title, i, codelists)


class Location(object):
    def __init__(self, elt):
        self.elt = elt
        self.point_re = re.compile(r"\s*([^\s]+)\s+([^\s]+)")

    def __repr__(self):
        return '''<Location: %s>''' % self.elt

    def get_elt_text(self, elt, key):
        # IATI 2.01
        res = elt.xpath(key + '/narrative/text()')
        if not res:
            # IATI 1.05
            res = elt.xpath(key + '/text()')
        return res

    def get_point(self, elt):
        point = elt.xpath('point/pos/text()')
        if point:
            res = self.point_re.match(point[0])
            if res:
                return res.groups()
        return elt.xpath('coordinates/@latitude'), elt.xpath('coordinates/@longitude')

    def to_dict(self):
        lat, lng = self.get_point(self.elt)
        data = {
            "name": self.get_elt_text(self.elt, 'name'),
            "description": self.get_elt_text(self.elt, 'description'),
            "latitude": lat,
            "longitude": lng,
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
            return '<div class="progress"><div class="progress-bar" style="width: ' + str(round(value,2)) + '%;"></div></div>'

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
        if elt is not None and elt.find("narrative") is not None:
            elt = elt.find("narrative")
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
        if elt is not None and elt.find("narrative") is not None:
            elt = elt.find("narrative")
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
        texts = [{'text': x} for x in self.elt.xpath('narrative/text()')]
        if len(texts) == 0:
            texts = [{'text': self.elt.text}]
        data = {
            "type": self.elt.xpath("@type"),
            "texts": texts,
            }
        return data


class Conditions(object):
    def __init__(self, xml_string):
        root = lxml.etree.fromstring(xml_string)
        self.root = root

    def get_conditions(self):
        return {
            'attached': self.root.xpath("conditions/@attached"),
            'conditions': [Condition(condition).to_dict() for condition in self.root.xpath('conditions/condition')]}


class ActivityInfo(object):
    def __init__(self, xml_string):
        self.root = lxml.etree.fromstring(xml_string)
        self.titles = self.elt_text_or_MISSING("title")
        self.descriptions = self.elt_text_or_MISSING("description")

    def elt_text_or_MISSING(self, key):
        elt = self.root.xpath('{}/narrative/text()'.format(key))
        if len(elt) > 0:
            return [{'text': x} for x in elt]
        elt = self.root.xpath('{}/text()'.format(key))
        if len(elt) > 0:
            return [{'text': x} for x in elt]
        return [{'text': 'MISSING'}]
