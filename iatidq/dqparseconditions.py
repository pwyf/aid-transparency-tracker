
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import re
import sys
from functools import partial
import models

mappings = []

def add(regex):
    def append_to_mappings(fn):
        global mappings
        mappings.append((re.compile(regex),fn))
        return fn
    return append_to_mappings

def add_partial(regex):
    def append_to_mappings(fn):
        global mappings
        def partial_fn(groups):
            return partial(fn, groups=groups)
        mappings.append((re.compile(regex), partial_fn))
        return fn
    return append_to_mappings

def parsePC(organisation_structures):

    def organisation_and_test_level(groups):
        like = '%' + groups[1] + '%'
        organisation = models.Organisation.query.filter_by(organisation_code=groups[0]).first()
        tests = db.session.query(
            models.Test.id, 
            models.Test.name, 
            models.Test.description
            ).filter(models.Test.name.like(like)).all()
        return organisation, tests

    @add_partial('(\S*) does not use (\S*) at activity level')
    def doesnt_use_at_activity_level(activity, groups):
        organisation, tests = organisation_and_test_level(groups)
        return {'organisation':organisation, 
                'tests': tests, 
                'operation': 0, 
                'condition': 'activity level', 
                'condition_value': 1}

    @add_partial('(\S*) does not use (\S*) at activity hierarchy (\d*)')
    def doesnt_use_at_activity_hierarchy(activity, groups):
        organisation, tests = organisation_and_test_level(groups)
        return {'organisation':organisation, 
                'tests': tests, 
                'operation': 0, 
                'condition': 'activity hierarchy', 
                'condition_value': groups[2]}

    @add('(.*)')
    def fail(line):
        return None

    test_functions = {}
    comment = re.compile('#')
    blank = re.compile('^$')
    for n, line in organisation_structures.items():
        line = line.strip('\n')
        number = n

        for mapping in mappings:
            m = mapping[0].match(line)
            if m:
                f = mapping[1](m.groups())
                if f == None:
                    print "Not implemented:"
                    print line
                else:
                    print "Implemented:"
                    test_functions[number] = f
                    print f
                break
    return test_functions

if __name__ == '__main__':
    organisation_structures = {"GB-1 does not use document-link at activity hierarchy 2", "44000 does not use default-tied-status at activity level"}
    print parsePC(organisation_structures)
