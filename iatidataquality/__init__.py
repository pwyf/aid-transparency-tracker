from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__.split('.')[0])
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app)

import api
import routes
