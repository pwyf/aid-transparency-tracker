
import unittest
import nose
import nose.tools

from iatidataquality import app

class TestWeb(unittest.TestCase):
    def setUp(self):
        self.foo = 1
        self.app = app.test_client()

    def tearDown(self):
        pass

    @nose.with_setup(setUp, tearDown)
    def test1(self):
        rv = self.app.get('/organisations/GB-1/')
        print rv.data
        assert "Publication" in rv.data
