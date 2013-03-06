import iatidataquality.models as models
import foxpath

def get_active_tests():
    for test in models.Test.query.filter(models.Test.active == True).all():
        yield test

def test_functions():
    return foxpath.generate_test_functions(get_active_tests())
