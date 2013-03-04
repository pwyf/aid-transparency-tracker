import os
import sys

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidataquality
from iatidataquality import db
import lxml.etree

def test_checktitle():
    test = iatidataquality.models.Test()
    test.name = "title/text() exists?"
    test.active = True
    test.description = "Does title exist?"
    test.test_group = "title"
    test.test_level=1
    db.session.add(test)
    db.session.commit()
    print "Wrote to DB, ID is",test.id

    from iatidataquality.dqparsetests import test_functions as tf
    test_functions = tf()

    data_files = [
        ("good.xml", True),
        ("bad.xml", False)
        ]

    def check_data_file(data_file, expected_result):
        parse_tree = lxml.etree.parse(os.path.join(current, data_file))
        activity = parse_tree.find('iati-activity')
        assert test_functions[test.id](activity) == expected_result

    [ check_data_file(data_file, expected_result)
      for data_file, expected_result in data_files ]

    db.session.delete(test)
    db.session.commit()
