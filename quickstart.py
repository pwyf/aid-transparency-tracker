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
#import warnings
#warnings.filterwarnings('error')

import iatidq

from iatidq import models, dqregistry 
import iatidq.dqfunctions
import iatidq.dqimporttests
import iatidq.dqdownload
import iatidq.dqimportcodelists
import iatidq.dqruntests
import iatidq.dqindicators

import optparse
import sys

which_packages = [
    (u'worldbank-tz', True),
    (u'unops-tz', True),
    (u'dfid-tz', True)
    ]

dfid_packages = {
  "dfid-ws": True, 
  "dfid-ls": True, 
  "dfid-lr": True, 
  "dfid-le": True, 
  "dfid-rw": True, 
  "dfid-la": True, 
  "dfid-lc": True, 
  "dfid-ru": True, 
  "dfid-lk": True, 
  "dfid-gb": True, 
  "dfid-ge": True, 
  "dfid-gh": True, 
  "dfid-gm": True, 
  "dfid-gn": True, 
  "dfid-gt": True, 
  "dfid-org": True, 
  "dfid-gy": True, 
  "dfid-vu": True, 
  "dfid-ot": True, 
  "dfid-vn": True, 
  "dfid-fa": True, 
  "dfid-89": True, 
  "dfid-fj": True, 
  "worldbank-tz": True, 
  "dfid-ms": True, 
  "dfid-jm": True, 
  "dfid-bt": True, 
  "dfid-br": True, 
  "dfid-bl": True, 
  "dfid-bj": True, 
  "dfid-bi": True, 
  "dfid-bf": True, 
  "dfid-798": True, 
  "dfid-bd": True, 
  "dfid-ug": True, 
  "dfid-ba": True, 
  "dfid-eb": True, 
  "dfid-ec": True, 
  "dfid-ea": True, 
  "dfid-ef": True, 
  "dfid-ed": True, 
  "dfid-er": True, 
  "dfid-et": True, 
  "dfid-380": True, 
  "dfid-mv": True, 
  "dfid-mw": True, 
  "dfid-tz": True, 
  "dfid-mz": True, 
  "dfid-ib": True, 
  "dfid-tr": True, 
  "dfid-tl": True, 
  "dfid-mg": True, 
  "dfid-md": True, 
  "dfid-tj": True, 
  "dfid-td": True, 
  "dfid-mn": True, 
  "dfid-tc": True, 
  "dfid-mm": True, 
  "dfid-dk": True, 
  "dfid-th": True, 
  "dfid-sl": True, 
  "dfid-sn": True, 
  "dfid-so": True, 
  "dfid-sh": True, 
  "dfid-sd": True, 
  "dfid-hn": True, 
  "dfid-ht": True, 
  "dfid-sq": True, 
  "dfid-ss": True, 
  "unops-tz": True, 
  "dfid-ke": True, 
  "dfid-kg": True, 
  "dfid-cv": True, 
  "dfid-ko": True, 
  "dfid-kh": True, 
  "dfid-cl": True, 
  "dfid-cm": True, 
  "dfid-cn": True, 
  "dfid-cd": True, 
  "dfid-cf": True, 
  "dfid-cg": True, 
  "dfid-rs": True, 
  "dfid-cb": True, 
  "dfid-zw": True, 
  "dfid-zz": True, 
  "dfid-za": True, 
  "dfid-zm": True, 
  "dfid-ni": True, 
  "dfid-298": True, 
  "dfid-289": True, 
  "dfid-na": True, 
  "dfid-ng": True, 
  "dfid-ne": True, 
  "dfid-null": True, 
  "dfid-ns": True, 
  "dfid-np": True, 
  "dfid-af": True, 
  "dfid-ua": True, 
  "dfid-ac": True, 
  "dfid-ao": True, 
  "dfid-al": True, 
  "dfid-as": True, 
  "dfid-ye": True, 
  "dfid-in": True, 
  "dfid-ph": True, 
  "dfid-pk": True, 
  "dfid-pn": True, 
  "dfid-cp": True, 
  "dfid-id": True, 
  "dfid-pe": True, 
  "dfid-pg": True, 
  "dfid-ps": True, 
  "dfid-iq": True, 
  "dfid-189": True, 
  "dfid-589": True
}

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
    p.add_option("--import_codelists", dest="import_codelists",
                 action="store_true",
                 default=False,
                 help="Import codelists")
    p.add_option("--enqueue-test", dest="enqueue_test",
                 action="store_true",
                 default=False,
                 help="Set a package to be tested (with --package)")
    p.add_option("--package", dest="package_name",
                 help="Set name of package to be tested")
    p.add_option("--filename", dest="filename",
                 help="Set filename of data to test")
    p.add_option("--local_folder", dest="local_folder",
                 help="Set local folder where data to test is stored")
    p.add_option("--all_dfid_packages", 
                 action="store_true",
                 dest="all_dfid_packages",
                 help="Test all DfID packages. --Local-folder must be provided.")
    p.add_option("--import_indicators", dest="import_indicators",
                 action="store_true",
                 default=False,
                 help="Import indicators. Will try to assign indicators to existing tests.")

    options, args = p.parse_args()

    if options.drop_all:
        iatidq.db.drop_all()
        return

    if options.init_db:
        iatidq.db.create_all()
        iatidq.dqimporttests.hardcodedTests()
        return

    if options.enroll_tests:
        filename = options.enroll_tests.decode()
        iatidq.dqimporttests.importTests(
            filename=filename, 
            level=options.level)
        return

    if options.clear_revisionid:
        iatidq.dqfunctions.clear_revisions()
        return

    if options.import_codelists:
        iatidq.dqimportcodelists.importCodelists()
        return

    if options.all_dfid_packages:
        assert options.local_folder
        for p in dfid_packages:
            print p
            package_name = p
            filename = options.local_folder + "/" + package_name + ".xml"
            iatidq.dqruntests.enqueue_package_for_test(filename,
                                                       package_name)
        return

    if options.download:
        if options.minimal_pkgs:
            for package_name, _ in which_packages:
                iatidq.dqdownload.run(package_name=package_name)
        else:
            iatidq.dqdownload.run()
        return

    if options.import_indicators:
        if options.filename:
            iatidq.dqindicators.importIndicators(filename=options.filename)
        else:
            iatidq.dqindicators.importIndicators()
        return

    if options.enqueue_test:
        assert options.package_name
        assert options.filename

        iatidq.dqruntests.enqueue_package_for_test(options.filename,
                                                   options.package_name)
        return

    run(refresh=options.refresh, minimal=options.minimal_pkgs)

if __name__ == '__main__':
    main()
