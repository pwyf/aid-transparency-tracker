#!/usr/bin/env python

""" This script is to quickly get started with this tool, by:
        1) creating DB
        2) populating the list of packages from the Registry (will download basic data about all packages)
        3) setting 3 to "active"
"""

import iatidataquality

from iatidataquality import models, dqregistry 
import iatidataquality.dqfunctions
import iatidataquality.dqimporttests

import optparse
import sys

iatidataquality.db.create_all()

def run(refresh):
    which_packages = [
                ('worldbank-tz', True),
                ('unops-tz', True),
                ('dfid-tz', True)
                ]
    if refresh:
        dqregistry.refresh_packages()
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

def main():
    p = optparse.OptionParser()
    p.add_option("--refresh", dest="refresh", action="store_true",
                 help="Don't refresh")
    p.add_option("--clear-revisionid", dest="clear_revisionid", 
                 action="store_true",
                 help="Clear CKAN revision ids")
    p.add_option("--init-db", dest="init_db",
                  action="store_true",
                  help="Initialise DB")
    p.add_option("--drop-db", dest="drop_all",
                  action="store_true",
                  help="Delete DB")
    p.add_option("--enroll-tests", dest="enroll_tests",
                 help="Enroll a CSV file of tests")
    p.add_option("--level", dest="level",
                 type="int",
                 default=1,
                 help="Test level (e.g., 1 == Activity)")

    options, args = p.parse_args()

    if options.drop_all:
        iatidataquality.db.drop_all()
        return

    if options.init_db:
        iatidataquality.db.create_all()
        iatidataquality.dqimporttests.hardcodedTests()
        return

    if options.enroll_tests:
        iatidataquality.dqimporttests.importTests(
            filename=options.enroll_tests, 
            level=options.level)
        return

    if options.clear_revisionid:
        iatidataquality.dqfunctions.clear_revisions()
        return

    run(refresh=options.refresh)

if __name__ == '__main__':
    main()
