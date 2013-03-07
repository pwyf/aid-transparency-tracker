
import sys, os, json, ckan, urllib2
import itertools
from datetime import date, datetime
import models, dqprocessing, dqparsetests, \
    dqfunctions, queue
import dqprocessing
from lxml import etree

from iatidataquality import db

# FIXME: this should be in config
download_queue='iati_tests_queue'

def aggregate_results(runtime, package_id):
    return dqprocessing.aggregate_results(runtime, package_id)

def test_activity(runtime_id, package_id, result_identifier, data, 
                  test_functions, result_hierarchy):
    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()
    # FIXME: is this even used?
    conditions = models.TestCondition.query.filter(
        models.TestCondition.active == True).all()

    def add_result(test_id, the_result):
        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        db.session.add(newresult)

    # | test_result == True  -> 1
    # | test_result == False -> 0
    # | exception            -> 2 (exceptions aren't counted against publishers)
    def execute_test(test_id):
        try:
            return int(test_functions[test_id](xmldata))
        except:
            return 2

    def execute_and_record(test):
        the_result = execute_test(test.id)
        add_result(test.id, the_result)

    test_exists = lambda t: t.id in test_functions
    tests = itertools.ifilter(test_exists, tests)
    
    [ execute_and_record(test) for test in tests ]

    return "Success"

def check_file(file_name, runtime_id, package_id, context=None):
    try:
        try:
            data = etree.parse(file_name)
        except etree.XMLSyntaxError:
            dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, False)
            return
        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, True)
        from dqparsetests import test_functions as tf
        test_functions = tf()

        def get_result_hierarchy(activity):
            hierarchy = activity.get('hierarchy', default=None)
            if hierarchy is "":
                return None
            return hierarchy

        for activity in data.findall('iati-activity'):
            result_hierarchy = get_result_hierarchy(activity)

            result_identifier = activity.find('iati-identifier').text
            activity_data = etree.tostring(activity)

            res = test_activity(runtime_id, package_id, 
                                result_identifier, activity_data, 
                                test_functions, result_hierarchy)

        db.session.commit()

        print "Aggregating results..."
        dqprocessing.aggregate_results(runtime_id, package_id)
        print "Finished aggregating results"
        db.session.commit()    

        dqfunctions.add_test_status(package_id, 3, commit=True)
    except Exception, e:
        print "Exception in check_file ", e

def dequeue_download(body):
    try:
        args = json.loads(body)
        check_file(args['filename'],
                  args['runtime_id'],
                  args['package_id'],
                  args['context'])
    except Exception, e:
        print "Exception in dequeue_download", e

def run_test_queue():
    for body in queue.handle_queue_generator(download_queue):
        dequeue_download(body)
