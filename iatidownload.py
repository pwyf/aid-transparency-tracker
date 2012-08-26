import sys
import ckan    
import urllib2
from datetime import date
import os
import models
import database

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

runtime = models.Runtime()
database.db_session.add(runtime)
database.db_session.commit()

def metadata_to_db(pkg, file):
    result = models.Result()
    result.test_id = -2
    result.runtime_id = runtime.id
    result.result_level = u'file'
    package = models.Package()
    if file:
        package.man_auto = 'auto'
        package.source_url = pkg['resources'][0]['url']
        package.package_ckan_id = pkg['id']
        package.package_name = pkg['name']
        package.package_title = pkg['title']
        database.db_session.add(package)
        database.db_session.commit()
        result.result_data = 1
        result.package_id = package.id
        database.db_session.add(result)
        database.db_session.commit()
    else:
        result.result_data = 0 

def run(directory):
    url = 'http://iatiregistry.org/api'
    import ckanclient
    registry = ckanclient.CkanClient(base_location=url)
    startnow = False
    for pkg_name in registry.package_register_get():
            pkg = registry.package_entity_get(pkg_name)
            for resource in pkg.get('resources', []):
                # This logic is flawed if this loop runs more than once
                # But this should not happen for IATI data
                try:
                    save_file(pkg_name, resource['url'], dir)
                    file = resource['url']
                except urllib2.URLError, e:
                    file = False
            metadata_to_db(pkg, file)
            print resource.get('url')

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
