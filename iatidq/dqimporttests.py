
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

def hardcodedTests():
    hardcoded_tests = [
        (-2, u'url_exists', u"Check that the xml file actually exists."),
        (-3, u'valid_xml', u"Check that xml is well structured"),
        (-4, u'schema_conformance', u"Check that xml conforms to schema")
    ]

    for hardcoded_test in hardcoded_tests:
        if models.Test.query.filter(models.Test.id==hardcoded_test[0]).first():
            continue
        test = models.Test()
        test.setup(
            name = hardcoded_test[1],
            description = hardcoded_test[2],
            test_group = None,
            test_level = 2,
            active = True,
            id = hardcoded_test[0]
            )
        db.session.add(test)
    db.session.commit()

def returnLevel(row, level):
    if (('level' in row) and (row['level'] != "")):
        return row['level']
    else:
        return level

def _importTests(fh, filename, level=1, local=True):
    data = unicodecsv.DictReader(fh)

    for row in data:
        test = models.Test.query.filter(models.Test.name==row['test_name']).first()

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
    db.session.commit()
    print "Imported successfully"
    return True

def importTestsFromFile(filename, level=1):
    with file(filename) as fh:
        return _importTests(fh, filename, level=level, local=True)

def importTestsFromUrl(url, level=1):
    fh = urllib2.urlopen(url)
    return _importTests(fh, url, level=level, local=False)
