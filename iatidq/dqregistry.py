
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import urllib2
import models
import json
import ckanclient

import util

from dqfunctions import packages_from_registry

REGISTRY_URL = "http://iatiregistry.org/api/2/search/dataset?fl=id,name,groups,title&offset=%s&limit=1000"

CKANurl = 'http://iatiregistry.org/api'

# pg is sqlalchemy model; ckangroup is a ckan object
def copy_pg_attributes(pg, ckangroup):
    mapping = [
        ("title", "title"),
        ("ckan_id", "id"),
        ("revision_id", "revision_id"),
        ("created_date", "created"),
        ("state", "state")
        ]
    for attr, key in mapping:
        try:
            setattr(pg, attr, ckangroup[key])
        except Exception, e:
            pass

# pg is sqlalchemy model; ckangroup is a ckan object
def copy_pg_misc_attributes(pg, ckangroup, handle_country):
    try:
        pg.license_id = ckangroup['extras']['publisher_license_id']
    except Exception, e:
        pass

    if handle_country:
        try:
            pg.package_country = ckangroup['extras']['country']
        except Exception, e:
            pass

# pg is sqlalchemy model; ckangroup is a ckan object
def copy_pg_fields(pg, ckangroup):
    fields = [
        'publisher_iati_id', 'publisher_segmentation', 'publisher_type', 
        'publisher_ui', 'publisher_organization_type', 
        'publisher_frequency', 'publisher_thresholds', 'publisher_units', 
        'publisher_contact', 'publisher_agencies', 
        'publisher_field_exclusions', 'publisher_description', 
        'publisher_record_exclusions', 'publisher_timeliness', 
        'publisher_country', 'publisher_refs', 
        'publisher_constraints', 'publisher_data_quality'
        ]

    for field in fields:
        try:
            setattr(pg, field, ckangroup['extras'][field])
        except Exception, e:
            pass

def create_package_group(group, handle_country=True):
    pg = models.PackageGroup()
    pg.name = group
    pg.man_auto = u"auto"
    
    # Query CKAN
    import ckanclient
    registry = ckanclient.CkanClient(base_location=CKANurl)
    ckangroup = registry.group_entity_get(group)

    copy_pg_attributes(pg, ckangroup)
    copy_pg_misc_attributes(pg, ckangroup, handle_country)
    copy_pg_fields(pg, ckangroup)

    db.session.add(pg)
    db.session.commit()
    return pg

# package: a sqla model; pkg: a ckan object
def setup_package_group(package, pkg):
    with util.report_error(None, "Error saving package_group"):
        # there is a group, so use that group ID, or create one
        group = pkg['groups'][0]
        pg = models.PackageGroup.query.filter_by(name=group).first()
        if pg is None:
            pg = create_package_group(group, handle_country=False)
        package.package_group = pg.id

# FIXME: compare this with similar function in download_queue

# pkg is sqlalchemy model; package is ckan object
def copy_pkg_attributes(pkg, package):
    components = [ 
        ("id","package_ckan_id"),
        ("name","package_name"),
        ("title","package_title")
        ]
    for attr, key in components:
        setattr(pkg, key, package[attr])
    
# Don't get revision ID; 
# empty var will trigger download of file elsewhere
def refresh_package(package):
    print package['name']
    pkg = models.Package.query.filter_by(
        package_name=package['name']).first()
    if (pkg is None):
        pkg = models.Package()

    copy_pkg_attributes(pkg, package)
    setup_package_group(pkg, package)

    pkg.man_auto = u'auto'
    db.session.add(pkg)
    db.session.commit()

def refresh_package_by_name(package_name):
    registry = ckanclient.CkanClient(base_location=CKANurl)  
    package = registry.package_entity_get(package_name)
    refresh_package(package)

def _refresh_packages():
    [ refresh_package(package) 
      for package in packages_from_registry(REGISTRY_URL) ]

def refresh_packages():
    with util.report_error(None, "Couldn't open Registry"):
        return _refresh_packages()

def activate_packages(data, clear_revision_id=None):
    for package_name, active in data:
        pkg = models.Package.query.filter_by(package_name=package_name).first()
        if (clear_revision_id is not None):
            pkg.package_revision_id = u""
        pkg.active = active
        db.session.add(pkg)
    db.session.commit()

if __name__ == "__main__":
    refresh_packages()
