
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import itertools
import json
import re
import urllib2

import ckanclient

from iatidataquality import app, db
from . import models, util


REGISTRY_TMPL = 'https://iatiregistry.org/api/3/action/package_search?start={}&rows=1000'

CKANurl = 'https://iatiregistry.org/api'


class PackageMissing(Exception): pass


def packages_from_iati_registry():
    offset = 0
    while True:
        registry_url = REGISTRY_TMPL.format(offset)
        data = urllib2.urlopen(registry_url, timeout=60).read()
        print(registry_url)
        data = json.loads(data)['result']

        if len(data['results']) == 0:
            break

        for pkg in data['results']:
            yield pkg

        offset += 1000

def _set_deleted_package(package, set_deleted=False):
    if package.deleted != set_deleted:
        with db.session.begin():
            package.deleted = set_deleted
            db.session.add(package)
        return True
    return False

def check_deleted_packages():
    offset = 0
    # all packages on IATI currently
    registry_packages = [x['id'] for x in packages_from_iati_registry()]
    # all packages in the database currently
    db_packages = models.Package.query.all()
    count_deleted = 0
    for pkg in db_packages:
        # Need to do both in case a package is deleted and then resurrected
        if pkg.package_ckan_id in registry_packages:
            _set_deleted_package(pkg, False)
        else:
            print "Should delete package", pkg.package_name
            if _set_deleted_package(pkg, True):
                count_deleted += 1
    return count_deleted


# pg is sqlalchemy model; ckangroup is a ckan object
def copy_pg_attributes(pg, ckangroup):
    mapping = {
        "title": "title",
        "ckan_id": "id",
        "revision_id": "revision_id",
        "created_date": "created",
        "state": "state",
    }
    for attr, key in mapping.items():
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
    with db.session.begin():
        pg = models.PackageGroup()
        pg.name = group
        pg.man_auto = u"auto"

        # Query CKAN
        registry = ckanclient.CkanClient(base_location=CKANurl)
        ckangroup = registry.group_entity_get(group)

        copy_pg_attributes(pg, ckangroup)
        copy_pg_misc_attributes(pg, ckangroup, handle_country)
        copy_pg_fields(pg, ckangroup)

        db.session.add(pg)
    return pg

# package: a sqla model; pkg: a ckan object
def setup_package_group(group):
    with util.report_error(None, "Error saving package_group"):
        # there is a group, so use that group name, or create one

        if group is not None:
            pg = models.PackageGroup.query.filter_by(name=group).first()
            if pg is None:
                pg = create_package_group(group, handle_country=False)
                print('Created new package group: {}'.format(group))
            return pg

# FIXME: compare this with similar function in download_queue

# pkg is sqlalchemy model; package is ckan object
def copy_pkg_attributes(pkg, package):
    components = {
        "id": "package_ckan_id",
        "name": "package_name",
        "title": "package_title",
    }
    for attr, key in components.items():
        setattr(pkg, key, package[attr])

# Don't get revision ID;
# empty var will trigger download of file elsewhere
def refresh_package(package):
    if package.get('organization') and package['organization'].get('name'):
        packagegroup_name = package['organization']['name']
    else:
        packagegroup_name = None

    # Setup packagegroup outside of package transaction
    packagegroup = setup_package_group(packagegroup_name)
    if packagegroup:
        packagegroup_id = packagegroup.id
    else:
        packagegroup_id = None

    with db.session.begin():
        print package['name']
        pkg = models.Package.query.filter_by(
            package_name=package['name']).first()
        if (pkg is None):
            pkg = models.Package()

        copy_pkg_attributes(pkg, package)
        pkg.package_group_id = packagegroup_id
        pkg.man_auto = u'auto'
        db.session.add(pkg)

def refresh_package_by_name(package_name):
    registry = ckanclient.CkanClient(base_location=CKANurl)
    try:
        package = registry.package_entity_get(package_name)
        refresh_package(package)
    except ckanclient.CkanApiNotAuthorizedError:
        print "Error 403 (Not authorised) when retrieving '%s'" % package_name
    except ckanclient.CkanApiNotFoundError:
        print "Error 404 (Not found) when retrieving '%s'" % package_name
        raise

def _refresh_packages():
    setup_orgs = app.config.get("SETUP_ORGS", [])
    counter = app.config.get("SETUP_PKG_COUNTER", None)

    for package in packages_from_iati_registry():
        package_name = package["name"]
        if len(setup_orgs):
            if [x for x in setup_orgs if package_name.startswith('{}-'.format(x))] == []:
                continue
        registry = ckanclient.CkanClient(base_location=CKANurl)
        package = registry.package_entity_get(package_name)

        refresh_package(package)
        if counter is not None:
            counter -= 1
            if counter <= 0:
                break

def matching_packages(regexp):
    r = re.compile(regexp)

    pkgs = packages_from_iati_registry()
    pkgs = itertools.ifilter(lambda i: r.match(i["name"]), pkgs)
    for package in pkgs:
        yield package["name"]

def refresh_packages():
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
