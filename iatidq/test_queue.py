
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

from iatidq import db, app
import test_level
import test_result
import package_status
import hardcoded_test

# FIXME: this should be in config
rm_results = app.config["REMOVE_RESULTS"]
download_queue='iati_tests_queue'

missing_result_id = 0

class InvalidXPath(Exception): pass
class MissingIdentifier(Exception): pass

def delete_results(runtime_id, package_id):
    with db.session.begin():
        results = models.Result.query.filter(
            models.Result.runtime_id==runtime_id,
            models.Result.package_id==package_id
            ).delete()

def get_result_identifier(activity):
    try:
        return activity.find('iati-identifier').text.decode()
    except:
        raise MissingIdentifier

def binary_test(test_name):
    if re.compile("(.*) is on list (.*)").match(test_name):
        return True
    return False

def tests_by_level(test_functions, level):
    tests = models.Test.query.filter(models.Test.active == True,
                                     models.Test.test_level == level).all()

    test_exists = lambda t: t.id in test_functions
    return itertools.ifilter(test_exists, tests)

def _test_elements(test_functions, codelists, add_result,
                  tests, data, override_result):

    def reformat_test_data(xmldata, binary_test):
        if binary_test:
            return {
                "activity": xmldata,
                "lists": codelists
                }
        else:
            return xmldata

    def execute_test(xmldata, test_id, binary_test):
        if override_result is not None:
            return override_result

        data = reformat_test_data(xmldata, binary_test)
        # FIXME: All tests should really be validated in some way before being 
        # entered into the database.
        try:
            result = test_functions[test_id](data)
            if result == True:
                return test_result.PASS
            elif result == None:
                return test_result.SKIP
            elif result == False:
                return test_result.FAIL
        except:
            return test_result.ERROR

    def execute_and_record(xmldata, test):
        the_result = execute_test(xmldata, test.id, binary_test(test.name))
        #if the_result != test_result.SKIP:
        if True:
            add_result(test.id, the_result)

    [ execute_and_record(data, test) for test in tests ]

def test_elements(xml_fragment, test_functions, codelists, add_result,
                  override_result):

    elements = etree.fromstring(xml_fragment)

    activity_tests = tests_by_level(test_functions, test_level.ACTIVITY)
    transaction_tests = tests_by_level(test_functions, test_level.TRANSACTION)

    activity_data = elements
    transaction_data = elements.xpath("transaction")

    tests_and_sources = [
        (activity_tests, activity_data),
        (transaction_tests, transaction_data)
        ]
    
    for tests, data in tests_and_sources:
        return _test_elements(test_functions, codelists, add_result,
                              tests, data, override_result)

def test_activity(runtime_id, package_id, activity, 
                  result_hierarchy, test_functions, codelists,
                  organisation_id):
    global missing_result_id

    override_result = None
    
    try:
        result_identifier = get_result_identifier(activity)
    except MissingIdentifier:
        override_result = test_result.FAIL
        missing_result_id += 1
        result_identifier = "MISSING-%d" % missing_result_id

    data = etree.tostring(activity)

    results = []

    def add_result(test_id, the_result):
        results.append((test_id, the_result))

    def add_results():
        with db.session.begin():
            for test_id, the_result in results:
                newresult = models.Result()
                newresult.runtime_id = runtime_id
                newresult.package_id = package_id
                newresult.test_id = test_id
                newresult.result_data = the_result
                newresult.result_identifier = result_identifier
                newresult.result_hierarchy = result_hierarchy
                newresult.organisation_id = organisation_id
                db.session.add(newresult)

    res = test_elements(data, test_functions, codelists, add_result, 
                        override_result)
    add_results()

def test_organisation_data(xml_fragment, test_functions, codelists, add_result):
    override_result = None

    organisation_data = etree.fromstring(xml_fragment)

    organisation_tests = tests_by_level(test_functions, test_level.ORGANISATION)

    tests_and_sources = [
        (organisation_tests, organisation_data)
        ]
    
    for tests, data in tests_and_sources:
        return _test_elements(test_functions, codelists, add_result,
                              tests, data, override_result)

def test_organisation(runtime_id, package_id, data, test_functions, codelists,
                  organisation_id):
    
    results = []

    def add_result(test_id, the_result):
        results.append((test_id, the_result))

    def add_results():
        with db.session.begin():
            for test_id, the_result in results:
                newresult = models.Result()
                newresult.runtime_id = runtime_id
                newresult.package_id = package_id
                newresult.test_id = test_id
                newresult.result_data = the_result
                newresult.result_identifier = None
                newresult.result_hierarchy = None
                newresult.organisation_id = organisation_id
                db.session.add(newresult)

    res = test_organisation_data(data, test_functions, codelists, add_result)
    add_results()

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
        
        test_activity(runtime_id, package_id, activity,
                      result_hierarchy,
                      test_functions, 
                      codelists, organisation_id)

    def run_test_organisation(organisation_id, 
                org_organisation_data):
        
        run_info_results(package_id, runtime_id, org_organisation_data, 
                test_level.ORGANISATION, organisation_id)
        organisation_data = etree.tostring(org_organisation_data)

        test_organisation(runtime_id, package_id, 
                organisation_data, test_functions, 
                codelists, organisation_id)

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

        if len(org_activities)>0:
            run_info_results(package_id, runtime_id, org_activities, 
                test_level.ACTIVITY, org_id)
        org_organisations_data = data.xpath('//iati-organisation')

        [ run_test_organisation(org_id, org_organisation_data) for 
            org_organisation_data in org_organisations_data]
        
    organisations = dqpackages.get_organisations_for_testing(package_id)
    assert len(organisations) > 0

    for organisation in organisations:
        run_tests_for_organisation(organisation)

    dqprocessing.aggregate_results(runtime_id, package_id)


    dqfunctions.add_test_status(package_id, package_status.TESTED)

def unguarded_check_file(test_functions, codelists, file_name, 
                runtime_id, package_id):
    xml_parsed, data = parse_xml(file_name)

    dqprocessing.add_hardcoded_result(hardcoded_test.VALID_XML, 
                                      runtime_id, package_id, xml_parsed)

    if not xml_parsed:
        print "XML parse failed"
        return False

    check_data(runtime_id, package_id, test_functions, codelists, data)

    if rm_results:
        delete_results(runtime_id, package_id)

    return True

def check_file(test_functions, codelists, file_name, 
                runtime_id, package_id):
    try:
        return unguarded_check_file(test_functions, codelists, file_name, 
                                    runtime_id, package_id)
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

def test_one_package(filename, package_name):
    import testrun

    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()
    
    package = models.Package.query.filter_by(
        package_name=package_name).first()
    package_id = package.id
    runtime_id = testrun.start_new_testrun().id

    print "Package: %s" % package_name
    print "Package ID: %d" % package_id
    print "Runtime: %d" % runtime_id

    check_file(test_functions, codelists,
               filename,
               runtime_id,
               package_id)
    

def run_test_queue():
    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()

    for body in queue.handle_queue_generator(download_queue):
        dequeue_download(body, test_functions, codelists)

def test_queue_once():
    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()

    callback_fn = lambda body: dequeue_download(body, test_functions, codelists)
    queue.exhaust_queue(download_queue, callback_fn)

def run_info_results(package_id, runtime_id, xmldata, level, organisation_id):
    import inforesult
    import inforesult_orgtests

    def add_info_result(info_id, result_data):
        with db.session.begin():
            ir = models.InfoResult()
            ir.runtime_id = runtime_id
            ir.package_id = package_id
            ir.organisation_id = organisation_id
            ir.info_id = info_id
            ir.result_data = result_data
            db.session.add(ir)
        
    def info_lam_by_name(name):
        hack = { 
            'coverage': lambda fn: inforesult.inforesult_total_disbursements_commitments(fn),
            'coverage_current': lambda fn: inforesult.inforesult_total_disbursements_commitments_current(fn),
            'total_budgets_available': lambda fn: inforesult_orgtests.total_budgets_available(fn),
            'total_country_budgets': lambda fn: inforesult_orgtests.total_country_budgets_single_result(fn),
            'country_strategy_papers': lambda fn: inforesult_orgtests.country_strategy_papers(fn)
            }
        return hack[name]

    try:
        info_types = models.InfoType.query.filter_by(level=level
                ).all()
        for it in info_types:
            lam = info_lam_by_name(it.name)
            try:
                result = lam(xmldata)
            except:
                import sys
                import traceback
                traceback.print_exc()
                result = 0
            add_info_result(it.id, result)

    finally:
        pass 
