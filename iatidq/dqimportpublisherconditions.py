
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import urllib.request, urllib.error, urllib.parse

from . import dqparseconditions


def _parsePCresults(results):
    test_functions = dqparseconditions.parsePC(results)
    tested_results = []
    for n, line in list(results.items()):
        data = test_functions[n](line)
        data["description"] = line
        tested_results.append(data)

    return tested_results

def importPCsFromText(text):
    results = {}
    for n, line in enumerate(text.split("\n")):
        if line != "\n":
            results[n]=line
    return _parsePCresults(results)

def _importPCs(fh, local=True):
    results = {}
    for n, line in enumerate(fh):
        line = line.decode()
        if line == "\n":
            continue
        if line.startswith('#'):
            continue
        text = line.strip('\n')
        results[n] = text
    return _parsePCresults(results)

def importPCsFromFile(filename='tests/organisation_structures.txt', local=True):
    with open(filename) as fh:
        return _importPCs(fh, local=True)

def importPCsFromUrl(url):
    fh = urllib.request.urlopen(url)
    return _importPCs(fh, local=False)

if __name__ == "__main__":
    importPCs('../tests/organisation_structures.txt')
