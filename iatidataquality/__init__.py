
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__.split('.')[0])
app.config.from_pyfile(os.path.join('..', 'config.py'))
db = SQLAlchemy(app, session_options={"autocommit":True})

from . import usermanagement
from . import api
from . import routes
from . import publisher_conditions
from . import tests
from . import organisations
from . import organisations_feedback
from . import registry
from . import packages
from . import indicators
from . import aggregationtypes
from . import surveys
from . import users
from . import sampling
from . import cli
