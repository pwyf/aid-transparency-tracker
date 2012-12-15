from db import *
import models, dqprocessing, dqparsetests
from lxml import etree

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

@app.route("/aggregate_results/<runtime>/")
@app.route("/aggregate_results/<runtime>/<commit>/")
def aggregate_results(runtime, commit=False):
    return dqprocessing.aggregate_results(runtime, commit)

def test_activity(runtime_id, package_id, result_identifier, data, test_functions, result_hierarchy):
    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()
    conditions = models.TestCondition.query.filter(models.TestCondition.active == True).all()
    
    for test in tests:
        if not test.id in test_functions:
            continue

        if test_functions[test.id](xmldata):
            the_result = 1
        else:
            the_result = 0

        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        db.session.add(newresult)
    return "Success"

def check_file(file_name, runtime_id, package_id, context=None):
    try:
        data = etree.parse(file_name)
    except etree.XMLSyntaxError:
        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, False)
        return
    dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, True)
    from dqparsetests import test_functions as tf
    test_functions = tf()
    for activity in data.findall('iati-activity'):
        try:
            result_hierarchy = activity.get('hierarchy')
        except KeyError:
            result_hierarchy = None
        result_identifier = activity.find('iati-identifier').text
        activity_data = etree.tostring(activity)
        res = test_activity(runtime_id, package_id, result_identifier, activity_data, test_functions, result_hierarchy)

@celery.task(name="iatidataquality.load_package", track_started=True)
def load_package(runtime):
    output = ""
    
    path = DATA_STORAGE_DIR()
    for package in models.Package.query.order_by(models.Package.id).all():
        print package.id
        output = output + ""
        output = output + "Loading file " + package.package_name + "...<br />"
        
        filename = path + '/' + package.package_name + '.xml'

        # run tests on file
        res = check_file(filename, runtime, package.id, None)

        output = output + 'Finished adding task </a>.<br />'
    db.session.commit()
    aggregate_results(runtime)
    db.session.commit()
    return output
