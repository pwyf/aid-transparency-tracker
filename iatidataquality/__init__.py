from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

#import dqfunctions, dqprocessing, dqruntests
#import dqdownload, dqregistry, queue

app = Flask(__name__.split('.')[0])
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app)

import api
import routes


def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

def clear_revisions():
    for pkg in models.Package.query.filter(
        models.Package.package_revision_id!=None, 
        models.Package.active == True
        ).all():

        pkg.package_revision_id = None
        
        db.session.add(pkg)
    db.session.commit()
