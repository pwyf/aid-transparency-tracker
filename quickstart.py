#!/usr/bin/env python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

""" This script is to quickly get started with this tool, by:
        1) creating DB
        2) populating the list of packages from the Registry (will download basic data about all packages)
        3) setting 3 to "active"
"""

import iatidq

from iatidq import models, dqregistry 
import iatidq.dqfunctions
import iatidq.dqimporttests
import iatidq.dqdownload

import optparse
import sys

which_packages = [
    ('worldbank-tz', True),
    ('unops-tz', True),
    ('dfid-tz', True)
    ]

def run(refresh=False, minimal=False):
    if refresh:
        if minimal:
            for package_name, _ in which_packages:
                dqregistry.refresh_package_by_name(package_name)
        else:
            dqregistry.refresh_packages()
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

def main():
    p = optparse.OptionParser()
    p.add_option("--refresh", dest="refresh", action="store_true",
                 help="Refresh")
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
    p.add_option("--minimal-pkgs", dest="minimal_pkgs",
                 action="store_true",
                 default=False,
                 help="Operate on a minimal set of packages")
    p.add_option("--download", dest="download",
                 action="store_true",
                 default=False,
                 help="Download packages")

    options, args = p.parse_args()

    if options.drop_all:
        iatidq.db.drop_all()
        return

    if options.init_db:
        iatidq.db.create_all()
        iatidq.dqimporttests.hardcodedTests()
        return

    if options.enroll_tests:
        iatidq.dqimporttests.importTests(
            filename=options.enroll_tests, 
            level=options.level)
        return

    if options.clear_revisionid:
        iatidq.dqfunctions.clear_revisions()
        return

    if options.download:
        if options.minimal_pkgs:
            for package_name, _ in which_packages:
                iatidq.dqdownload.run(package_name=package_name)
        else:
            iatidatq.dqdownload.run()
        return

    run(refresh=options.refresh, minimal=options.minimal_pkgs)

if __name__ == '__main__':
    main()
