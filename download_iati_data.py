import sys
import ckan    
import urllib2
from datetime import date, datetime
import os
from iatidataquality import models, db

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

def metadata_to_db(pkg, file, update_package):
    result = models.Result()
    result.test_id = -2
    result.runtime_id = runtime.id
    result.result_level = u'file'
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
        package.package_group = pkg['groups'][0]
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
    db.session.add(package)
    db.session.commit()
    result.package_id = package.id
    if file:
        result.result_data = 1
    else:
        result.result_data = 0 
    db.session.add(result)


def run(directory):
    url = 'http://iatiregistry.org/api'
    import ckanclient
    registry = ckanclient.CkanClient(base_location=url)
    startnow = False
    for pkg_name in registry.package_register_get():
            pkg = registry.package_entity_get(pkg_name) 
            new_package = False
            update_package = False
            # Check if package already exists; if it has not been updated more recently than the database, then download it again
            check_package = models.Package.query.filter_by(package_ckan_id=pkg['id']).first()
            if (check_package):
            # found a package
                if ((check_package.package_metadata_modified) != (datetime.strptime(pkg['metadata_modified'], "%Y-%m-%dT%H:%M:%S.%f"))):
                    # if the package has been updated, then download it and update the package data
                    update_package = True
                    print "Updating package"
            else:
                # package not already downloaded
                new_package = True
                update_package = False

            if (update_package or new_package):
                # Download the file
                for resource in pkg.get('resources', []):
                    # This logic is flawed if this loop runs more than once
                    # But this should not happen for IATI data

                    try:
                        save_file(pkg_name, resource['url'], dir)
                        file = resource['url']
                    except urllib2.URLError, e:
                        file = False
                metadata_to_db(pkg, file, update_package)
                print resource['url']
            else:
                print "Already have package", pkg["name"]

def save_file(pkg_name, url, dir):
    localFile = open(dir + '/' + pkg_name + '.xml', 'w')
    webFile = urllib2.urlopen(url)
    localFile.write(webFile.read())
    webFile.close()
    localFile.close()

if __name__ == '__main__':
    import sys
    thetransactions = []
    dir = 'data'
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except Exception, e:
            print "Failed:", e
            print "Couldn't create directory"
    run(dir)
