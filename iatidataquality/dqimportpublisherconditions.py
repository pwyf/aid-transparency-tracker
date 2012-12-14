from db import *
import models
import csv
import urllib2


def importPCs(filename='tests/publisher_structures.txt', local=True):
    #models.Test.query.filter(models.Test.test_level==1).update({models.Test.active: False})

    if (local==True):
        f = open(filename, 'r')
    else:
        try:
            f = urllib2.urlopen(filename, timeout=60)
        except:
            return False
    
    results = []
    for n, line in enumerate(open(filename)):
        text = line.strip('\n')
        results.append(line)
        
    print "Parsed successfully"
    import dqparseconditions
    test_functions = dqparseconditions.parsePC(results)
    tested_results = []
    for tf in test_functions:
        tested_results.append(tf(results[0]))
    return tested_results

if __name__ == "__main__":
    importPCs('../tests/publisher_structures.txt')
