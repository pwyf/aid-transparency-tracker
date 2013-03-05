#!/usr/bin/env python

# this line must precede ckan import
import config

import sys, os, json, ckan, urllib2, ckanclient
from datetime import date, datetime
from iatidataquality import models, db, dqruntests, queue
from iatidataquality.dqprocessing import add_hardcoded_result
from iatidataquality.dqregistry import create_package_group
from iatidataquality.util import report_error

# FIXME: this should be in config
download_queue = 'iati_download_queue'
CKANurl = 'http://iatiregistry.org/api'

def fixURL(url):
    # helper function to replace spaces with %20 
    # (otherwise fails with some servers, e.g. US)
    url = url.replace(" ", "%20")
    return url

def metadata_to_db(pkg, package_name, success, runtime_id):
    try:
        package = models.Package.query.filter_by(
            package_name=package_name).first()

        package.man_auto = 'auto'
        package.source_url = pkg['resources'][0]['url']

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
            try:
                setattr(package, attr, pkg[key])
            except Exception:
                pass

        try:
            # there is a group, so use that group ID, or create one
            group = pkg['groups'][0]
            try:
                pg = models.PackageGroup.query.filter_by(name=group).first()
                package.package_group = pg.id
            except Exception, e:
                pg = create_package_group(group, handle_country=False)
                package.package_group = pg.id
        except Exception, e:
            pass

        fields = [ 
            "activity_period-from", "activity_period-to",
            "activity_count", "country", "filetype", "verified" 
            ]
        for field in fields:
            try:
                field_name = "package_" + field.replace("-", "_")
                setattr(package, field_name, pkg["extras"][field])
            except Exception, e:
                pass

        db.session.add(package)
        db.session.commit()
        add_hardcoded_result(-2, runtime_id, package.id, success)
    except Exception, e:
        print "Error in metadata_to_db:", e

def actually_save_file(package_name, orig_url, pkg, runtime_id):
    # `pkg` is a CKAN dataset
    success = False
    directory = config.DATA_STORAGE_DIR

    print "Attempting to fetch package", package_name, "from", orig_url
    url = fixURL(orig_url)

    try:
        path = os.path.join(directory, package_name + '.xml')
        with file(path, 'w') as localFile:
            webFile = urllib2.urlopen(url)
            localFile.write(webFile.read())
            webFile.close()
            success = True
            print "  Downloaded, processing..."
    except urllib2.URLError, e:
        success = False
        print "  Couldn't fetch URL"

    with report_error("  Wrote metadata to DB", 
                      "  Couldn't write metadata to DB"):
        metadata_to_db(pkg, package_name, success, runtime_id)

    with report_error("  Package tested",
                      "  Couldn't test package %s" % package_name):
        dqruntests.start_testing(package_name)

def save_file(package_id, package_name, runtime_id):
    registry = ckanclient.CkanClient(base_location=CKANurl)   
    try:
        pkg = registry.package_entity_get(package_name)
        resources = pkg.get('resources', [])
    except Exception, e:
        print "Couldn't get URL from CKAN for package", package_name, e
        return

    if resources == []:
        return
    if len(resources) > 1:
        print "WARNING: multiple resources found; attempting to use first"

    url = resources[0]['url']

    with report_error(None, None):
        actually_save_file(package_name, url, pkg, runtime_id)

def dequeue_download(body):
    args = json.loads(body)
    try:
        save_file(args['package_id'],
                  args['package_name'],
                  args['runtime_id'])
    except Exception:
        print sys.exc_info()
        print "Exception!!", e
        print


def callback_fn(ch, method, properties, body):
    dequeue_download(body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    print "Starting up..."
    directory = config.DATA_STORAGE_DIR
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception, e:
            print "Failed:", e
            print "Couldn't create directory"
    while True:
        queue.handle_queue(download_queue, callback_fn)

