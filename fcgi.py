#!/usr/bin/python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flup.server.fcgi import WSGIServer
from iatidataquality import app

if __name__ == '__main__':
    WSGIServer(app, bindAddress='fcgi.sock', umask=0).run()
