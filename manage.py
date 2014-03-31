#!/usr/bin/env python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask.ext.script import Manager, Server
import iatidataquality
import iatidq.dqimporttests

def run():
    iatidq.db.create_all()
    iatidq.dqimporttests.hardcodedTests()
    manager = Manager(iatidataquality.app)
    server = Server(host='0.0.0.0')
    manager.add_command("runserver", server)
    manager.run()

if __name__ == "__main__":
    run()
