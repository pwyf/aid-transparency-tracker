
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import models

class TestNotFound(Exception): pass

def tests(test_id=None):
    if test_id is not None:
        checkTests = models.Test.query.filter_by(id=test_id).first_or_404()
    else:
        checkTests = models.Test.query.order_by(models.Test.id).all()

    if checkTests:
        return checkTests
    else:
        return False

def test_by_test_name(test_name=None):
    checkTest = models.Test.query.filter_by(name=test_name).first()
    if not checkTest:
        raise TestNotFound
    return checkTest

def updateTest(data):
    checkTest = tests(data['id'])
    if checkTest:
        with db.session.begin():
            for k, v in data.items():
                setattr(checkTest, k, v)
            db.session.add(checkTest)
        return checkTest
    else:
        return False

def deleteTest(test_id):
    with db.session.begin():
        checkTest = tests(test_id)
        db.session.delete(checkTest)

def addTest(data):
    try:
        checkTest = test_by_test_name(data["name"])
    except TestNotFound:
        return False

    with db.session.begin():
        test = models.Test()
        test.setup(
            name = data['name'],
            description = data['description'],
            test_group = "",
            test_level = data['test_level'],
            active = data['active']
            )
        db.session.add(test)
    return test
