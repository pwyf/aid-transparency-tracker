
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

app = Flask(__name__.split('.')[0])
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.login_view = 'account.signin'
login_manager.login_message = u"Please sign in to access this page."
login_manager.setup_app(app)

class User(object):
    pass

@login_manager.user_loader
def load_user(userid):
    if userid == "admin":
        return User()
    else:
        return None

import api
import routes
