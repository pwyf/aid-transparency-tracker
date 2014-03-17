
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models
import csv
import util
import urllib2

def _parsePCresults(results):
    import dqparseconditions
    test_functions = dqparseconditions.parsePC(results)
    tested_results = []
    for n, line in results.items():
        data = test_functions[n](line)
        data["description"] = line
        tested_results.append(data)

    return tested_results

def importPCsFromText(text):
    results = {}
    for n, line in enumerate(text.split("\n")):
        results[n]=line
    return _parsePCresults(results)

def _importPCs(fh, local=True):
    results = {}
    for n, line in enumerate(fh):
        text = line.strip('\n')
        results[n]=text
    return _parsePCresults(results)

def importPCsFromFile(filename='tests/organisation_structures.txt', local=True):
    with file(filename) as fh:
        return _importPCs(fh, local=True) 

def importPCsFromUrl(url):
    fh = urllib2.urlopen(url)
    return _importPCs(fh, local=False)

if __name__ == "__main__":
    importPCs('../tests/organisation_structures.txt')
