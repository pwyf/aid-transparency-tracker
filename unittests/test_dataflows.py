import os
import sys
import csv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidq

import nose
import nose.tools

import json
import uuid

import iatidq.dqregistry
from iatidq import db
from iatidq import models

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
    with file('unittests/artefacts/json/pkgdata-worldbank-tz.json') as f:
        package = json.load(f)
    iatidq.dqregistry.refresh_package(package)

    pkg = models.Package.query.filter_by(
        package_name=package['name']).first()
    assert pkg is not None

    new_title = "Retitled package"
    assert new_title != pkg.package_title

    package['title'] = new_title
    iatidq.dqregistry.refresh_package(package)
    
    pkg = models.Package.query.filter_by(
        package_name=package['name']).first()

    assert new_title == pkg.package_title
