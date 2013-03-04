import os
import sys

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidataquality
from iatidataquality import db
import lxml.etree

def create_tst(name):
    test = iatidataquality.models.Test()
    test.name = name
    test.active = True
    test.description = "Test FN"
    test.test_group = "???"
    test.test_level=1
    db.session.add(test)
    db.session.commit()
    return test

def remove_tst(test):
    db.session.delete(test)
    db.session.commit()

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

    remove_tst(test)

def test_checktitle():
    tests = [
        "title/text() exists?",
        "description/text() exists?"
        ]

    [ check_against_files(test) for test in tests ]
