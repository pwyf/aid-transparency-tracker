
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidataquality import db

import models
import csv
import urllib2


def importPCs(filename='tests/publisher_structures.txt', local=True):
    #models.Test.query.filter(models.Test.test_level==1).update({models.Test.active: False})

    if (local==True):
        f = open(filename)
    else:
        try:
            f = urllib2.urlopen(filename, timeout=60)
        except:
            return False
    
    results = {}
    for n, line in enumerate(f):
        text = line.strip('\n')
        results[n]=text
        #results.append(text)
        
    import dqparseconditions
    test_functions = dqparseconditions.parsePC(results)
    tested_results = []
    for n, line in results.items():
        data = test_functions[n](line)
        data["description"] = line
        tested_results.append(data)

    return tested_results

if __name__ == "__main__":
    importPCs('../tests/publisher_structures.txt')
