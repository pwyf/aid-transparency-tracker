
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import re
import urllib.request, urllib.error, urllib.parse

import yaml

from iatidataquality import db
from . import hardcoded_test, models, test_level


def hardcodedTests():
    hardcoded_tests = [
        (hardcoded_test.URL_EXISTS,
         'url_exists', "Check that the xml file actually exists."),
        (hardcoded_test.VALID_XML,
         'valid_xml', "Check that xml is well structured"),
        (hardcoded_test.SCHEMA_CONFORMANCE,
         'schema_conformance', "Check that xml conforms to schema")
    ]

    with db.session.begin():
        for hc_test in hardcoded_tests:
            if models.Test.query.filter(models.Test.id == hc_test[0]).first():
                continue
            test = models.Test()
            test.setup(
                name=hc_test[1],
                description=hc_test[2],
                test_group=None,
                test_level=test_level.FILE,
                active=True,
                id=hc_test[0]
                )
            db.session.add(test)


def returnLevel(row, level):
    if (('test_level' in row) and (row['test_level'] != "")):
        return row['test_level']
    else:
        return level


def _importTests(fh, filename, level=1, local=True):
    data = yaml.safe_load(fh)
    # indicators = [i for c in data['components'] for i in c['indicators']]

    line_num = 0
    for indicator in data['indicators']:
        indicator_name = indicator['name'].lower()
        indicator_name = re.sub(r'[\(\)\s/-]+', '-', indicator_name)
        for row in indicator['tests']:
            line_num += 1
            with db.session.begin():
                test = models.Test.query.filter(
                    models.Test.description == row['name']).first()

                if not test:
                    test = models.Test()

                test.setup(
                    description=row['name'],
                    test_group=indicator_name,
                    test_level=returnLevel(row, level),
                    active=True
                )
                test.file = filename
                test.line = line_num
                db.session.add(test)

            with db.session.begin():
                test = models.Test.query.filter(
                    models.Test.description == row['name']).first()

                if indicator_name:
                    ind = models.Indicator.query.filter(
                        models.Indicator.name == indicator_name).first()

                    assert ind
                    assert test
                    assert test.id

                    newIT = models.IndicatorTest.query.filter(
                        models.IndicatorTest.test_id == test.id).first()
                    if not newIT:
                        newIT = models.IndicatorTest()
                    newIT.setup(
                        indicator_id=ind.id,
                        test_id=test.id
                        )
                    db.session.add(newIT)

    line_num += 1
    row = data['filter']
    with db.session.begin():
        test = models.Test.query.filter(
            models.Test.description == row['name']).first()

        if not test:
            test = models.Test()

        test.setup(
            description=row['name'],
            test_group='',
            test_level=returnLevel(row, level),
            active=True
        )
        test.file = filename
        test.line = line_num
        db.session.add(test)

    print("Imported successfully")
    return True


def importTestsFromFile(filename, level):
    with open(filename) as fh:
        return _importTests(fh, filename, level=level, local=True)


def importTestsFromUrl(url, level=1):
    fh = urllib.request.urlopen(url)
    return _importTests(fh, url, level=level, local=False)
