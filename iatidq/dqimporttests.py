
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import models
import unicodecsv

import util

import test_level
import hardcoded_test

def hardcodedTests():
    hardcoded_tests = [
        (hardcoded_test.URL_EXISTS, 
         u'url_exists', u"Check that the xml file actually exists."),
        (hardcoded_test.VALID_XML, 
         u'valid_xml', u"Check that xml is well structured"),
        (hardcoded_test.SCHEMA_CONFORMANCE,
         u'schema_conformance', u"Check that xml conforms to schema")
    ]

    with db.session.begin():
        for hc_test in hardcoded_tests:
            if models.Test.query.filter(models.Test.id==hc_test[0]).first():
                continue
            test = models.Test()
            test.setup(
                name = hc_test[1],
                description = hc_test[2],
                test_group = None,
                test_level = 2,
                active = True,
                id = hc_test[0]
                )
            db.session.add(test)

def returnLevel(row, level):
    if (('test_level' in row) and (row['test_level'] != "")):
        return row['test_level']
    else:
        return level

def _importTests(fh, filename, level=1, local=True):
    data = unicodecsv.DictReader(fh)
    
    for row in data:
        with db.session.begin():
            test = models.Test.query.filter(
                models.Test.name==row['test_name']).first()

            if not test:
                test = models.Test()

            test.setup(
                name = row['test_name'],
                description = row['test_description'],
                test_group = row['indicator_name'],
                test_level = returnLevel(row, level),
                active = True
                )
            test.file = filename
            test.line = data.line_num
            db.session.add(test)

        with db.session.begin():
            test = models.Test.query.filter(
                models.Test.name==row['test_name']).first()

            if row['indicator_name']:
                ind = models.Indicator.query.filter(
                    models.Indicator.name==row['indicator_name']).first()

                assert ind
                assert test
                assert test.id

                newIT = models.IndicatorTest()
                newIT.setup(
                    indicator_id = ind.id,
                    test_id = test.id
                    )
                db.session.add(newIT)

    print "Imported successfully"
    return True

def importTestsFromFile(filename, level):
    with file(filename) as fh:
        return _importTests(fh, filename, level=level, local=True)

def importTestsFromUrl(url, level=1):
    fh = urllib2.urlopen(url)
    return _importTests(fh, url, level=level, local=False)
