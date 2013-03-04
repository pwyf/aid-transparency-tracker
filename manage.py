#!/usr/bin/env python
from flask.ext.script import Manager
import iatidataquality
import iatidataquality.dqimporttests

def run():
    iatidataquality.db.create_all()
    iatidataquality.dqimporttests.hardcodedTests()
    manager = Manager(iatidataquality.app)
    manager.run()

if __name__ == "__main__":
    run()
