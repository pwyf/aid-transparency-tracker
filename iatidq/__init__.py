
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

# obviously this is a hack on a stick; we shouldn't be depending on
# flask, but this is quicker than googling the runes for SQLAlchemy

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__.split('.')[0])
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app, session_options={"autocommit":True})

