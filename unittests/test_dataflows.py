import json

import nose
import nose.tools

from iatidataquality import db
from iatidq import dqregistry, models


def setup_func():
    with db.session.begin():
        for pkg in models.Package.query.filter_by(
            package_name="testbank-tz").all():
            db.session.delete(pkg)

def teardown_func():
    with db.session.begin():
        for pkg in models.Package.query.filter_by(
            package_name="testbank-tz").all():
            db.session.delete(pkg)

@nose.with_setup(setup_func, teardown_func)
def test_change_title():
    with open('unittests/artefacts/json/pkgdata-worldbank-tz.json') as f:
        package = json.load(f)
    dqregistry.refresh_package(package)

    pkg = models.Package.query.filter_by(
        package_name=package['name']).first()
    assert pkg is not None

    new_title = "Retitled package"
    assert new_title != pkg.package_title

    package['title'] = new_title
    dqregistry.refresh_package(package)

    pkg = models.Package.query.filter_by(
        package_name=package['name']).first()

    assert new_title == pkg.package_title
