
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import os

app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
db = SQLAlchemy(app)

import usermanagement
import api
import routes
import publisher_conditions
import tests
import organisations
import organisations_feedback
import registry
import packages
import indicators
import aggregationtypes
import surveys
import users
import sampling
