#!/usr/bin/env python
import sys
import ckan    
import urllib2
from datetime import date, datetime
import os
from iatidataquality import models, db,  DATA_STORAGE_DIR
from iatidataquality.dqprocessing import add_hardcoded_result
import json
import daemon

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

download_queue = 'iati_download_queue'
import pika

def fixURL(url):
    # helper function to replace spaces with %20 (otherwise fails with some servers, e.g. US)
    url = url.replace(" ", "%20")
    return url

def create_package_group(group):
    pg = models.PackageGroup()
    pg.name = group
    pg.man_auto="auto"
    
    # Query CKAN
    url = 'http://iatiregistry.org/api'
    import ckanclient
    registry = ckanclient.CkanClient(base_location=url)
    startnow = False
    ckangroup = registry.group_entity_get(group)
    pg.title = ckangroup['title']
    pg.ckan_id = ckangroup['id']
    pg.revision_id = ckangroup['revision_id']
    pg.created_date = ckangroup['created']
    try:
        pg.state = ckangroup['state']
    except Exception, e:
        pass
    try:
        pg.publisher_iati_id = ckangroup['extras']['publisher_iati_id']
    except Exception, e:
        pass
    try:
        pg.publisher_segmentation = ckangroup['extras']['publisher_segmentation']
    except Exception, e:
        pass
    try:
        pg.publisher_type = ckangroup['extras']['publisher_type']
    except Exception, e:
        pass
    try:
        pg.publisher_ui = ckangroup['extras']['publisher_ui']
    except Exception, e:
        pass
    try:
        pg.publisher_organization_type = ckangroup['extras']['publisher_organization_type']
    except Exception, e:
        pass
    try:
        pg.publisher_frequency = ckangroup['extras']['publisher_frequency']
    except Exception, e:
        pass
    try:
        pg.publisher_thresholds = ckangroup['extras']['publisher_thresholds']
    except Exception, e:
        pass
    try:
        pg.publisher_units = ckangroup['extras']['publisher_units']
    except Exception, e:
        pass
    try:
        pg.publisher_contact = ckangroup['extras']['publisher_contact']
    except Exception, e:
        pass
    try:
        pg.publisher_agencies = ckangroup['extras']['publisher_agencies']
    except Exception, e:
        pass
    try:
        pg.publisher_field_exclusions = ckangroup['extras']['publisher_field_exclusions']
    except Exception, e:
        pass
    try:
        pg.publisher_description = ckangroup['extras']['publisher_description']
    except Exception, e:
        pass
    try:
        pg.publisher_record_exclusions = ckangroup['extras']['publisher_record_exclusions']
    except Exception, e:
        pass
    try:
        pg.publisher_timeliness = ckangroup['extras']['publisher_timeliness']
    except Exception, e:
        pass
    try:
        pg.license_id = ckangroup['extras']['publisher_license_id']
    except Exception, e:
        pass
    try:
        pg.publisher_country = ckangroup['extras']['publisher_country']
    except Exception, e:
        pass
    try:
        pg.publisher_refs = ckangroup['extras']['publisher_refs']
    except Exception, e:
        pass
    try:
        pg.publisher_constraints = ckangroup['extras']['publisher_constraints']
    except Exception, e:
        pass
    try:
        pg.publisher_data_quality = ckangroup['extras']['publisher_data_quality']
    except Exception, e:
        pass

    db.session.add(pg)
    db.session.commit()
    return pg

def metadata_to_db(pkg, success, update_package):
    if (update_package):
        package = models.Package.query.filter_by(package_ckan_id=pkg['id']).first()
    else:
        package = models.Package()
    package.man_auto = 'auto'
    package.source_url = pkg['resources'][0]['url']
    package.package_ckan_id = pkg['id']
    package.package_name = pkg['name']
    package.package_title = pkg['title']
    package.package_license_id = pkg['license_id']
    package.package_license = pkg['license']
    package.package_metadata_created = pkg['metadata_created']
    package.package_metadata_modified = pkg['metadata_modified']
    try:
        # there is a group, so use that group ID, or create one
        group = pkg['groups'][0]
        try:
            pg = models.PackageGroup.query.filter_by(name=group).first()
            package.package_group = pg.id
        except Exception, e:
            pg = create_package_group(group)
            package.package_group = pg.id                
    except Exception, e:
        pass
    try:
        if pkg['extras']['activity_period-from']:
            package.package_activity_from = pkg['extras']['activity_period-from']
    except Exception, e:
        pass
    try:
        if pkg['extras']['activity_period-to']:
            package.package_activity_to = pkg['extras']['activity_period-to']
    except Exception, e:
        pass
    try:
        package.package_activity_count = pkg['extras']['activity_count']
    except Exception, e:
        pass
    try:
        package.package_country = pkg['extras']['country']
    except Exception, e:
        pass
    try:
        package.package_filetype = pkg['extras']['filetype']
    except Exception, e:
        pass
    try:
        package.package_verified = pkg['extras']['verified']
    except Exception, e:
        pass
    try:
        package.package_revision_id = pkg['revision_id']
    except Exception, e:
        pass
    db.session.add(package)
    db.session.commit()
    add_hardcoded_result(-2, runtime.id, package.id, success)


def save_file(pkg_name, filename, pkg, update_package):
    success = False
    directory = DATA_STORAGE_DIR()
    url = fixURL(filename)
    try:
        path = os.path.join(directory, pkg_name + '.xml')
        with file(path, 'w') as localFile:
            webFile = urllib2.urlopen(url)
            localFile.write(webFile.read())
            webFile.close()
            success = True
    except urllib2.URLError, e:
        success = False
        print "couldn't get file"
    metadata_to_db(pkg, success, update_package)
    print filename

def dequeue_download(body):
    args = json.loads(body)
    save_file(args['pkg_name'],
              args['file'],
              args['pkg'],
              args['update_package'])
    # notify queue that we finished properly


def get_connection(host):
    count = 0.4
    while count < 60:
        try:            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            return connection
        except:
            time.sleep(count)
            count *= 1.7
    sys.exit(1)

def handle_queue(queue_name, callback_fn):
    try:
        connection = get_connection('localhost')
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(callback_fn, queue=queue_name)

        channel.start_consuming()
    except:
        pass 
    finally:
        connection.close()

def callback_fn(ch, method, properties, body):
    dequeue_download(body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    directory = DATA_STORAGE_DIR()
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception, e:
            print "Failed:", e
            print "Couldn't create directory"
#   with daemon.DaemonContext(files_preserve=files_preserve):
    while True:
        handle_queue(download_queue, callback_fn)

