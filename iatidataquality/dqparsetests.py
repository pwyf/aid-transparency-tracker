import iatidataquality.models as models
import foxpath

from iatidataquality import db

def get_active_tests():
    for test in models.Test.query.filter(models.Test.active == True).all():
        yield test

def test_functions():
    try:
        return foxpath.generate_test_functions(get_active_tests())
    finally:
        db.session.commit()
