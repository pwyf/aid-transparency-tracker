from flask.ext.script import Manager
from flask.ext.celery import install_commands as install_celery_commands

from iatidataquality import app, db

db.create_all()
manager = Manager(app)
install_celery_commands(manager)

if __name__ == "__main__":
    manager.run()
