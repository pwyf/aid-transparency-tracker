from iatidataquality import db

import urllib2
import models
import json

import util

from dqfunctions import packages_from_registry

REGISTRY_URL = "http://iatiregistry.org/api/2/search/dataset?fl=id,name,groups,title&offset=%s&limit=1000"

CKANurl = 'http://iatiregistry.org/api'

def create_package_group(group, handle_country=True):
    pg = models.PackageGroup()
    pg.name = group
    pg.man_auto="auto"
    
    # Query CKAN
    import ckanclient
    registry = ckanclient.CkanClient(base_location=CKANurl)
    ckangroup = registry.group_entity_get(group)

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

    try:
        pg.license_id = ckangroup['extras']['publisher_license_id']
    except Exception, e:
        pass

    if handle_country:
        try:
            pg.package_country = ckangroup['extras']['country']
        except Exception, e:
            pass

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

    db.session.add(pg)
    db.session.commit()
    return pg

def _refresh_packages():
    # Don't get revision ID; 
    # empty var will trigger download of file elsewhere
    components = [ ("id","package_ckan_id"),
                   ("name","package_name"),
                   ("title","package_title")
                   ]

    def refresh_package(package):
        print package['name']
        pkg = models.Package.query.filter_by(
            package_name=package['name']).first()
        if (pkg is None):
            pkg = models.Package()
        for attr, key in components:
            setattr(pkg, key, package[attr])
        try:
            # there is a group, so use that group ID, or create one
            group = package['groups'][0]
            try:
                pg = models.PackageGroup.query.filter_by(
                    name=group).first()
                pkg.package_group = pg.id
            except Exception, e:
                pg = create_package_group(group)
                pkg.package_group = pg.id
        except Exception, e:
            pass
        pkg.man_auto = 'auto'
        db.session.add(pkg)
        db.session.commit()

    [ refresh_package(package) 
      for package in packages_from_registry(REGISTRY_URL) ]


def refresh_packages():
    with util.report_error(None, "Couldn't open Registry"):
        return _refresh_packages()

def activate_packages(data, clear_revision_id=None):
    for package_name, active in data:
        pkg = models.Package.query.filter_by(package_name=package_name).first()
        if (clear_revision_id is not None):
            pkg.package_revision_id = ""
        pkg.active = active
        db.session.add(pkg)
    db.session.commit()

if __name__ == "__main__":
    refresh_packages()
