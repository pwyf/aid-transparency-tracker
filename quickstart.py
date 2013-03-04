#!/usr/bin/env python

""" This script is to quickly get started with this tool, by:
        1) creating DB
        2) populating the list of packages from the Registry (will download basic data about all packages)
        3) setting 3 to "active"
"""

import iatidataquality

from iatidataquality import models, dqregistry, clear_revisions

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
    p.add_option("--dont-refresh", dest="dont_refresh", action="store_true",
                 help="Don't refresh")
    p.add_option("--clear-revisionid", dest="clear_revisionid", 
                 action="store_true",
                 help="Clear CKAN revision ids")
    options, args = p.parse_args()

    if options.clear_revisionid:
        clear_revisions()
        return

    run(refresh=options.dont_refresh)

if __name__ == '__main__':
    main()
