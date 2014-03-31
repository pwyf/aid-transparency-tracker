
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import sys, os, json, ckan, ckanclient
from datetime import date, datetime
import models, dqruntests, queue
from dqprocessing import add_hardcoded_result
from dqregistry import setup_package_group
from util import report_error, download_file

from iatidq import db, app
import hardcoded_test

# FIXME: this should be in config
download_queue = 'iati_download_queue'
CKANurl = 'http://iatiregistry.org/api'

def fixURL(url):
    # helper function to replace spaces with %20 
    # (otherwise fails with some servers, e.g. US)
    url = url.replace(" ", "%20")
    return url

# package: a sqla model; pkg: a ckan object
def copy_package_attributes(package, pkg):
    mapping = [
        ("package_ckan_id", "id"),
        ("package_name", "name"),
        ("package_title", "title"),
        ("package_license_id", "license_id"),
        ("package_license", "license"),
        ("package_metadata_created", "metadata_created"),
        ("package_metadata_modified", "metadata_modified"),
        ("package_revision_id", "revision_id")
        ]

    for attr, key in mapping:
        with report_error(None, None):
            setattr(package, attr, pkg[key])

# package: a sqla model; pkg: a ckan object
def copy_package_fields(package, pkg):
    fields = [ 
        "activity_period-from", "activity_period-to",
        "activity_count", "country", "filetype", "verified" 
        ]
    for field in fields:
        with report_error(None, None):
            field_name = "package_" + field.replace("-", "_")
            setattr(package, field_name, pkg["extras"][field])

def metadata_to_db(pkg, package_name, success, runtime_id):
    with db.session.begin():
        package = models.Package.query.filter_by(
            package_name=package_name).first()

        package.man_auto = 'auto'
        package.source_url = pkg['resources'][0]['url']
        package.hash = pkg['resources'][0]['hash']

        if pkg.get('organization') and pkg['organization'].get('name'):
            packagegroup_name = pkg['organization']['name']
        else:
            packagegroup_name = None
        packages_groups = {pkg['name']: packagegroup_name}

        copy_package_attributes(package, pkg)
        setup_package_group(package, pkg, packages_groups)
        copy_package_fields(package, pkg)

        db.session.add(package)

    add_hardcoded_result(hardcoded_test.URL_EXISTS, 
                         runtime_id, package.id, success)

def manage_download(path, url):
    # report_error mangles return values; so we don't use it here
    try:
        download_file(url, path)
        print "  Downloaded, processing..."
        return True
    except Exception, e:
        print "  Couldn't fetch URL", e
        return False

def actually_save_file(package_name, orig_url, pkg, runtime_id):
    # `pkg` is a CKAN dataset
    success = False
    directory = app.config['DATA_STORAGE_DIR']

    print "Attempting to fetch package", package_name, "from", orig_url
    url = fixURL(orig_url)
    path = os.path.join(directory, package_name + '.xml')

    success = manage_download(path, url)

    with report_error("  Wrote metadata to DB", 
                      "  Couldn't write metadata to DB"):
        metadata_to_db(pkg, package_name, success, runtime_id)

    with report_error("  Package tested",
                      "  Couldn't test package %s" % package_name):
        dqruntests.start_testing(package_name)

def actually_save_manual_file(package_name):
    success = False
    directory = app.config['DATA_STORAGE_DIR']

    package = models.Package.query.filter_by(
        package_name=package_name).first()

    url = fixURL(package.source_url)
    path = os.path.join(directory, package_name + '.xml')

    success = manage_download(path, url)

    with db.session.begin():
        package.hash = 'retrieved'
        db.session.add(package)

    with report_error("  Package tested",
                      "  Couldn't test package %s" % package_name):
        dqruntests.start_testing(package_name)


def save_file(package_id, package_name, runtime_id, man_auto):
    if man_auto == 'auto':
        print "Trying to get auto package"
        registry = ckanclient.CkanClient(base_location=CKANurl)
        try:
            pkg = registry.package_entity_get(package_name)
            resources = pkg.get('resources', [])
        except Exception, e:
            print "Couldn't get URL from CKAN for package", package_name, e
            return

        print package_id, package_name, runtime_id
        if resources == []:
            return
        if len(resources) > 1:
            print "WARNING: multiple resources found; attempting to use first"

        url = resources[0]['url']
        print url

        with report_error("Saving %s" % url, None):
            actually_save_file(package_name, url, pkg, runtime_id)
    else:
        with report_error("Saving %s" % package_name, None):
            actually_save_manual_file(package_name)

def dequeue_download(body):
    args = json.loads(body)
    try:
        save_file(args['package_id'],
                  args['package_name'],
                  args['runtime_id'],
                  args['man_auto'])
    except Exception:
        print sys.exc_info()
        print "Exception!!", e
        print


def callback_fn(ch, method, properties, body):
    dequeue_download(body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

def run_download_queue():
    while True:
        queue.handle_queue(download_queue, callback_fn)

def download_queue_once():
    queue.exhaust_queue(download_queue, dequeue_download)
