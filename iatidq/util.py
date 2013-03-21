
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import contextlib
import os
import urllib2

@contextlib.contextmanager
def report_error(success, failure):
    try:
        yield
        if success is not None:
            print success
    except Exception, e:
        if failure is not None:
            print failure, e
    finally:
        pass

def ensure_download_dir(directory):
    if not os.path.exists(directory):
        with report_error(None, "Couldn't create directory"):
            os.makedirs(directory)

def download_file(url, path):
    with file(path, 'w') as localFile:
        webFile = urllib2.urlopen(url)
        localFile.write(webFile.read())
        webFile.close()
