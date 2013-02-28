from flask.ext.script import Manager
from iatidataquality import app, db, dqimporttests

db.create_all()
dqimporttests.hardcodedTests()
manager = Manager(app)

if __name__ == "__main__":
    manager.run()
