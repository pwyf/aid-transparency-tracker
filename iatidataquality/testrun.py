from iatidataquality import db
import models

def start_new_testrun():
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    return newrun
