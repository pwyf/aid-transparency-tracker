
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, app

import urllib2
import models
import json
import ckanclient

import util

from dqfunctions import packages_from_iati_registry, get_package_organisations

REGISTRY_URL = "http://iatiregistry.org/api/2/search/dataset?fl=id,name,groups,title&offset=%s&limit=1000"

CKANurl = 'http://iatiregistry.org/api'

IATIUPDATES_URL = 'http://tracker.publishwhatyoufund.org/iatiupdates/api/package/hash/'

class PackageMissing(Exception): pass

def _set_deleted_package(package_ckan_id, set_deleted=False):
    with db.session.begin():
        p = models.Package.query.filter(
            models.Package.package_ckan_id==package_ckan_id
            ).first()
        if p:        
            p.deleted = set_deleted
            db.session.add(p)
        return True
    return False

def check_deleted_packages():
    data = urllib2.urlopen(IATIUPDATES_URL, timeout=60).read()
    print IATIUPDATES_URL
    data = json.loads(data)
    count_deleted = 0
    for pkg in data['data']:
        # Need to do both in case a package is deleted and then resurrected
        if pkg['deleted'] == True:
            print "Should delete package", pkg['name']
            _set_deleted_package(pkg['id'], True)
            count_deleted +=1
        else:            
            _set_deleted_package(pkg['id'], False)
    return count_deleted
    

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
    return pg

# package: a sqla model; pkg: a ckan object
def setup_package_group(package, pkg, packages_groups):
    with util.report_error(None, "Error saving package_group"):
        # there is a group, so use that group ID, or create one

        group = packages_groups.get(package.package_name)
        if group is not None:
            pg = models.PackageGroup.query.filter_by(name=group).first()
            if pg is None:
                pg = create_package_group(group, handle_country=False)
                print "Created new group"
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
def refresh_package(package, packages_groups):
    with db.session.begin():
        print package['name']
        pkg = models.Package.query.filter_by(
            package_name=package['name']).first()
        if (pkg is None):
            pkg = models.Package()

        copy_pkg_attributes(pkg, package)
        setup_package_group(pkg, package, packages_groups)

        pkg.man_auto = u'auto'
        db.session.add(pkg)

def refresh_package_by_name(package_name):
    registry = ckanclient.CkanClient(base_location=CKANurl)
    try:
        package = registry.package_entity_get(package_name)
        if package.get('organization') and package['organization'].get('name'):
            packagegroup_name = package['organization']['name']
        else:
            packagegroup_name = None
        packages_groups = {package['name']: packagegroup_name}
        refresh_package(package, packages_groups)
    except ckanclient.CkanApiNotAuthorizedError:
        print "Error 403 (Not authorised) when retrieving '%s'" % package_name
    except ckanclient.CkanApiNotFoundError:
        print "Error 404 (Not found) when retrieving '%s'" % package_name
        raise
        
def _refresh_packages():
    setup_orgs = app.config.get("SETUP_ORGS", [])
    counter = app.config.get("SETUP_PKG_COUNTER", None)

    packages_groups = get_package_organisations(app.config["IATIUPDATES_URL"])

    for package in packages_from_iati_registry(REGISTRY_URL):
        package_name = package["name"]
        if len(setup_orgs) and ('-' in package_name):
            org, country = package_name.split('-', 1)
            if org not in setup_orgs:
                continue
        registry = ckanclient.CkanClient(base_location=CKANurl)
        pkg = registry.package_entity_get(package_name)
        refresh_package(pkg, packages_groups)
        if counter is not None:
            counter -= 1
            if counter <= 0:
                break

def matching_packages(regexp):
    import re
    import itertools
    r = re.compile(regexp)

    pkgs = packages_from_iati_registry(REGISTRY_URL)
    pkgs = itertools.ifilter(lambda i: r.match(i["name"]), pkgs)
    for package in pkgs:
        yield package["name"]

def refresh_packages():
    with util.report_error(None, "Couldn't open Registry"):
        return _refresh_packages()

def activate_packages(data, clear_revision_id=None):
    with db.session.begin():
        for package_name, active in data:
            pkg = models.Package.query.filter_by(package_name=package_name).first()
            if pkg is None:
                msg = "Package: %s found on CKAN, not in DB" % package_name
                raise PackageMissing(msg)
            if (clear_revision_id is not None):
                pkg.package_revision_id = u""
            pkg.active = active
            db.session.add(pkg)

def clear_hash(package_name):
    with db.session.begin():
        pkg = models.Package.query.filter_by(package_name=package_name).first()
        pkg.hash = ""
        pkg.package_metadata_modified = ""
        db.session.add(pkg)

if __name__ == "__main__":
    refresh_packages()
