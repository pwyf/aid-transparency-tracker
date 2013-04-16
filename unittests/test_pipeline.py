#!/usr/bin/python

import os
import sys
import csv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidq
import iatidq.dqparsetests
import iatidq.dqregistry

from iatidq import db
import lxml.etree

import nose
import nose.tools

from iatidq.models import *

def setup_func():
    iatidq.db.drop_all()
    iatidq.db.create_all()
    db.session.commit()

def teardown_func():
    pass

@nose.with_setup(setup_func, teardown_func)
def test_refresh():
    publisher = 'dfid'
    country = 'tz'
    package_name = '-'.join([publisher, country])

    # check there's nothing in the db
    pgs = iatidq.models.PackageGroup.query.filter(PackageGroup.name==publisher).all()
    assert len(pgs) == 0
    pkgs = iatidq.models.PackageGroup.query.filter(Package.package_name==package_name).all()
    assert len(pkgs) == 0

    # do refresh
    iatidq.dqregistry.refresh_package_by_name(package_name)

    # check there's something in the db
    pgs = iatidq.models.PackageGroup.query.filter(PackageGroup.name==publisher).all()
    assert len(pgs) == 1
    pg = pgs[0]
    assert pg.name == publisher

    pkgs = iatidq.models.Package.query.filter(Package.package_name==package_name).all()
    assert len(pkgs) == 1
    pkg = pkgs[0]
    assert pkg.package_name == package_name
