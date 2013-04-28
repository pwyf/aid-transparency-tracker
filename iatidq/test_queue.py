
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import sys, os, json, ckan
import itertools
from datetime import date, datetime
import models, dqprocessing, dqparsetests, dqpackages
import dqfunctions, queue
import dqprocessing
from lxml import etree
import re

from iatidq import db
import test_level
import test_result
import package_status
import hardcoded_test

# FIXME: this should be in config
download_queue='iati_tests_queue'

class InvalidXPath(Exception): pass


def binary_test(test_name):
    if re.compile("(\S*) is on list (\S*)").match(test_name):
        return True
    return False

def tests_by_level(test_functions, level):
    tests = models.Test.query.filter(models.Test.active == True,
                                     models.Test.test_level == level).all()

    test_exists = lambda t: t.id in test_functions
    return itertools.ifilter(test_exists, tests)

def test_activity(runtime_id, package_id, result_identifier, 
                  result_hierarchy, data, test_functions, codelists,
                  organisation_id):

    def add_result(test_id, the_result):
        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        newresult.organisation_id = organisation_id
        db.session.add(newresult)

    def execute_test(xmldata, test_id, binary_test):
        if binary_test:
            data = {
                "activity": xmldata,
                "lists": codelists
                }
        else:
            data = xmldata
        try:
            if test_functions[test_id](data):
                return test_result.PASS
            else:
                return test_result.FAIL
        except:
            return test_result.ERROR

    def execute_and_record(xmldata, test):
        the_result = execute_test(xmldata, test.id, binary_test(test.name))
        add_result(test.id, the_result)


    xmldata = etree.fromstring(data)

    activity_tests = tests_by_level(test_functions, test_level.ACTIVITY)
    transaction_tests = tests_by_level(test_functions, test_level.TRANSACTION)

    activity_data = xmldata
    transaction_data = xmldata.xpath("//transaction")

    tests_and_sources = [
        (activity_tests, activity_data),
        (transaction_tests, transaction_data)
        ]

    for tests, data in tests_and_sources:
        [ execute_and_record(data, test) for test in tests ]

def parse_xml(file_name):
    try:
        data = etree.parse(file_name)
        return True, data
    except etree.XMLSyntaxError:
        return False, None

def check_data(runtime_id, package_id, test_functions, codelists, data):
    def get_result_hierarchy(activity):
        hierarchy = activity.get('hierarchy', default=None)
        if hierarchy is "":
            return None
        return hierarchy

    def run_test_activity(organisation_id, activity):
        result_hierarchy = get_result_hierarchy(activity)
            
        result_identifier = activity.find('iati-identifier').text.decode()
        activity_data = etree.tostring(activity)
        
        test_activity(runtime_id, package_id, 
                      result_identifier, result_hierarchy,
                      activity_data, test_functions, 
                      codelists, organisation_id)
        db.session.commit()

    def get_activities(organisation):
        xp = organisation['activities_xpath']
        try:
            return data.xpath(xp)
        except etree.XPathEvalError:
            raise InvalidXPath(xp)

    def run_tests_for_organisation(organisation):
        org_activities = get_activities(organisation)
        org_id = organisation['organisation_id']

        [ run_test_activity(org_id, activity) 
          for activity in org_activities ]
        
    organisations = dqpackages.get_organisations_for_testing(package_id)
    assert len(organisations) > 0

    for organisation in organisations:
        run_tests_for_organisation(organisation)

    dqprocessing.aggregate_results(runtime_id, package_id)
    db.session.commit()    

    run_info_results(package_id, runtime_id, data)

    dqfunctions.add_test_status(package_id, package_status.TESTED, commit=True)

def check_file(test_functions, codelists, file_name, 
                runtime_id, package_id):
    try:
        xml_parsed, data = parse_xml(file_name)

        print file_name

        dqprocessing.add_hardcoded_result(hardcoded_test.VALID_XML, 
                                          runtime_id, package_id, xml_parsed)
        db.session.commit()

        if not xml_parsed:
            print "XML parse failed"
            return False

        check_data(runtime_id, package_id, test_functions, codelists, data)

        return True
    except Exception, e:
        import traceback
        traceback.print_exc()
        print "Exception in check_file ", e
        raise

def dequeue_download(body, test_functions, codelists):
    try:
        args = json.loads(body)
        check_file(test_functions, 
                   codelists,
                   args['filename'],
                   args['runtime_id'],
                   args['package_id'])
    except Exception, e:
        print "Exception in dequeue_download", e

def run_test_queue():
    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()

    for body in queue.handle_queue_generator(download_queue):
        dequeue_download(body, test_functions, codelists)

def run_info_results(package_id, runtime_id, xmldata):
    import inforesult

    def add_info_result(info_id, result_data):
        ir = models.InfoResult()
        ir.runtime_id = runtime_id
        ir.package_id = package_id
        ir.info_id = info_id
        ir.result_data = result_data
        db.session.add(ir)

    def info_lam_by_name(name):
        hack = { 
            'coverage': lambda fn: inforesult.infotest1(fn),
            'total_budget': lambda fn: inforesult.infotest2(fn)
            }
        return hack[name]

    try:
        info_types = models.InfoType.query.all()
        for it in info_types:
            lam = info_lam_by_name(it.name)
            try:
                result = lam(xmldata)
            except:
                import sys
                import traceback
                traceback.print_exc()
                result = None
            add_info_result(it.id, result)

    finally:
        db.session.commit()
