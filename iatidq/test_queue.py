
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import sys, os, json, ckan, urllib2
import itertools
from datetime import date, datetime
import models, dqprocessing, dqparsetests, dqpackages
import dqfunctions, queue
import dqprocessing
from lxml import etree
import re

from iatidq import db
import test_level

# FIXME: this should be in config
download_queue='iati_tests_queue'

class InvalidXPath(Exception): pass

def get_organisations_for_testing(package_id):
    organisations = []
    conditions = []
    packageorganisations = dqpackages.packageOrganisations(package_id)

    if packageorganisations:
        for packageorganisation in packageorganisations:
            # add organisations to be tested;
            organisation_id = packageorganisation.Organisation.id
            condition = packageorganisation.OrganisationPackage.condition
            if condition is not None:
                condition = "[" + condition.strip() + "]"
                conditions.append(condition)
            else:
                condition = ""

            organisations.append({
            'organisation_id': organisation_id,
            'activities_xpath': "//iati-activity%s" % condition
                            })

        conditions_str = " or ".join(conditions)
        remainder_xpath = "//iati-activity[not(%s)]" % conditions_str

        if conditions:
            organisations.append({
                    'organisation_id': None,
                    'activities_xpath': remainder_xpath
                    })
    if len(organisations) == 0:
        organisations.append({
                'organisation_id': None,
                'activities_xpath': "//iati-activity"
                })

    return organisations

def binary_test(test_name):
    if re.compile("(\S*) is on list (\S*)").match(test_name):
        return True
    return False

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

    # | test_result == True  -> 1
    # | test_result == False -> 0
    # | exception            -> 2 (exceptions aren't counted against publishers)
    def execute_test(xmldata, test_id, binary_test):
        try:
            if binary_test:
                data = {
                    "activity": xmldata,
                    "lists": codelists
                }
            else:
                data = xmldata
            return int(test_functions[test_id](data))
        except:
            return 2

    def execute_and_record(xmldata, test):
        the_result = execute_test(xmldata, test.id, binary_test(test.name))
        add_result(test.id, the_result)

    def tests_by_level(level):
        tests = models.Test.query.filter(models.Test.active == True,
                                         models.Test.test_level == level).all()

        test_exists = lambda t: t.id in test_functions
        return itertools.ifilter(test_exists, tests)

    xmldata = etree.fromstring(data)
    activity_tests = tests_by_level(test_level.ACTIVITY)

    [ execute_and_record(xmldata, test) for test in activity_tests ]

    transaction_tests = tests_by_level(test_level.TRANSACTION)
    #print xmldata
    for data in xmldata.xpath("//transaction"):
        [ execute_and_record(data, test) for test in transaction_tests ]

    return "Success"

def parse_xml(file_name):
    try:
        data = etree.parse(file_name)
        return True, data
    except etree.XMLSyntaxError:
        return False, None

def check_file(test_functions, codelists, file_name, 
                runtime_id, package_id, context=None):
    try:
        xml_parsed, data = parse_xml(file_name)

        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, 
                                           xml_parsed)
        db.session.commit()

        organisations = get_organisations_for_testing(package_id)
        #TODO: Implement for each organisation.
        # This is a bit crude because it only works for
        # iati-activities, and not organisation files.
        # But it's sufficient for now.

        if not xml_parsed:
            print "XML parse failed"
            return False

        def get_result_hierarchy(activity):
            hierarchy = activity.get('hierarchy', default=None)
            if hierarchy is "":
                return None
            return hierarchy

        def run_test_activity(organisation_id, activity):
            result_hierarchy = get_result_hierarchy(activity)
            
            result_identifier = activity.find('iati-identifier').text.decode()
            activity_data = etree.tostring(activity)

            res = test_activity(runtime_id, package_id, 
                                result_identifier, result_hierarchy,
                                activity_data, test_functions, 
                                codelists, organisation_id)
            db.session.commit()

        print "testing ..."

        assert len(organisations) > 0
        for organisation in organisations:
            xp = organisation['activities_xpath']
            try:
                org_activities = data.xpath(xp)
            except etree.XPathEvalError:
                raise InvalidXPath(xp)
            org_id = organisation['organisation_id']

            [ run_test_activity(org_id, activity) 
              for activity in org_activities ]

        print file_name

        print "Aggregating results..."
        dqprocessing.aggregate_results(runtime_id, package_id)
        print "Finished aggregating results"
        db.session.commit()    
        print "committed to db"

        run_info_results(package_id, runtime_id, file_name)

        dqfunctions.add_test_status(package_id, 3, commit=True)
        print "added test status"
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
                   args['package_id'],
                   args['context'])
    except Exception, e:
        print "Exception in dequeue_download", e

def run_test_queue():
    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()

    for body in queue.handle_queue_generator(download_queue):
        dequeue_download(body, test_functions, codelists)

def run_info_results(package_id, runtime_id, file_name):
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
                result = lam(file_name)
            except:
                import sys
                import traceback
                traceback.print_exc()
                result = None
            add_info_result(it.id, result)

    finally:
        db.session.commit()
