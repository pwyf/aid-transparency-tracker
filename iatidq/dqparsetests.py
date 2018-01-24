
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import itertools
from os.path import join
import re

from foxpath import Foxpath

from . import dqcodelists, models, test_level
from iatidataquality import db


comment = re.compile('#')
blank = re.compile('^$')


def ignore_line(line):
    return bool(comment.match(line) or blank.match(line))


def get_active_tests():
    for test in models.Test.query.filter(models.Test.active == True).all():
        yield test


def test_functions():
    with db.session.begin():
        codelists = dqcodelists.generateCodelists()
        tests = get_active_tests()
        tests = itertools.ifilter(lambda test: test.test_level != test_level.FILE, tests)
        tests = itertools.ifilter(lambda test: not ignore_line(test.name), tests)
        tests = [
            (x.id, 'Feature: {name}\nScenario: {name}\n{expression}'.format(
                name=x.id, expression=x.name))
            for x in tests]

        step_definitions_file = join('tests', 'step_definitions.py')
        foxpath = Foxpath(step_definitions_file)
        foxtests = {
            test[0]: foxpath.load_feature(test[1], codelists=codelists)[1][0][1]
            for test in tests}
        return foxtests
