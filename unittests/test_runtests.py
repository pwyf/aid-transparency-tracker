import os
import sys
import csv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidataquality
import iatidataquality.dqparsetests

from iatidataquality import db
import lxml.etree

import nose
import nose.tools

TEST_GROUP = "TEST_TEST"

def setup_func():
    tests = iatidataquality.models.Test.query.filter_by(
        test_group=TEST_GROUP).all()
    for test in tests:
        db.session.delete(test)
    db.session.commit()

def teardown_func():
    tests = iatidataquality.models.Test.query.filter_by(
        test_group=TEST_GROUP).all()
    for test in tests:
        db.session.delete(test)
    db.session.commit()

def create_tst(name):
    test = iatidataquality.models.Test()
    test.name = name
    test.active = True
    test.description = "Test FN"
    test.test_group = "TEST_TEST"
    test.test_level=1
    db.session.add(test)
    db.session.commit()
    return test

def check_against_files(test_str):
    test = create_tst(test_str)
    from iatidataquality.dqparsetests import test_functions as tf
    test_functions = tf()

    data_files = [
        ("good.xml", True),
        ("bad.xml", False)
        ]

    def check_data_file(data_file, expected_result):
        parse_tree = lxml.etree.parse(os.path.join(current, data_file))
        activity = parse_tree.find('iati-activity')
        observed = test_functions[test.id](activity)
        print observed, expected_result
        assert observed == expected_result

    [ check_data_file(data_file, expected_result)
      for data_file, expected_result in data_files ]

@nose.tools.raises(iatidataquality.foxpath.TestSyntaxError)
def check_data_files_w_tst_syntax_error(test_str):
    return check_against_files(test_str)

@nose.tools.raises(lxml.etree.XPathEvalError)
def check_data_files_w_xpath_eval_error(test_str):
    return check_against_files(test_str)

@nose.with_setup(setup_func, teardown_func)
def test_do_checks():
    tests = [
        "title/text() exists?",
        "description/text() exists?",
        ]

    [ check_against_files(test) for test in tests ]

@nose.with_setup(setup_func, teardown_func)
def test_checks_from_csv():
    filename = os.path.join(os.path.dirname(__file__),
                            "activity_tests.csv")

    with file(filename) as f:
        reader = csv.reader(f)
        header = reader.next() # i.e., discard first line
        for test_str, description, group in reader:
            yield check_against_files, test_str


@nose.with_setup(setup_func, teardown_func)
def test_invalid_xpath_syntax():
    tests = [
        "description/text) exists?",
        ]

    for test_str in tests:
        yield check_data_files_w_xpath_eval_error, test_str

@nose.with_setup(setup_func, teardown_func)
def test_unrecognised_syntaxes():
    tests = [
        "description/text) existz?"
        ]

    for test_str in tests:
        yield check_data_files_w_tst_syntax_error, test_str
