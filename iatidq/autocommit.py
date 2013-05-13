
from iatidq import db

do_commit = True

def commit():
    if do_commit:
        db.session.commit()
