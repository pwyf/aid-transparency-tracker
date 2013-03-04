#!/usr/bin/env python
from iatidataquality import models, db, DATA_STORAGE_DIR, dqruntests

def run():
    taskid = dqruntests.start_testing()
    print "Running, testing the following packages " + str(taskid)

if __name__ == '__main__':
    run()
