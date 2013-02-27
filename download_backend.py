#!/usr/bin/env python
import sys, os, json, ckan, pika, urllib2
from datetime import date, datetime
from iatidataquality import models, db, DATA_STORAGE_DIR, dqruntests
from iatidataquality.dqprocessing import add_hardcoded_result

runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

download_queue = 'iati_download_queue'

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

def metadata_to_db(pkg, success, update_package, runtime_id):
    if (update_package):
        package = models.Package.query.filter_by(package_ckan_id=pkg['id']).first()
    else:
        package = models.Package()
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
            pg = create_package_group(group)
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

def save_file(package_id, package_name, pkg, filename, update_package, runtime_id):
    # `package` is models.Packaege
    # `pkg` is a CKAN dataset
    # `filename` is the url of the file
    try:
        success = False
        directory = DATA_STORAGE_DIR()
        print "Attempting to fetch package", package_name, "from", filename
        url = fixURL(filename)
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
        try:
            metadata_to_db(pkg, success, update_package, runtime_id)
            print "  Wrote metadata to DB"
        except Exception, e:
            print "  Couldn't write metadata to DB"
        try:
            dqruntests.start_testing(package_name)
            print "  Package tested"
        except Exception, e:
            print "  Couldn't test package",package_name,e
    except Exception, e:
        pass

def dequeue_download(body):
    args = json.loads(body)
    try:
        save_file(args['package_id'],
                  args['package_name'],
                  args['pkg'],
                  args['url'],
                  args['update_package'],
                  args['runtime_id'])
    except Exception:
        print "Exception!!", e

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
    print "Starting up..."
    directory = DATA_STORAGE_DIR()
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception, e:
            print "Failed:", e
            print "Couldn't create directory"
    while True:
        handle_queue(download_queue, callback_fn)

