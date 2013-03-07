#!/usr/bin/env python

# this line must precede ckan import
import config
from iatidataquality.test_queue import run_test_queue
from iatidataquality.util import ensure_download_dir

if __name__ == '__main__':
    print "Starting up..."
    directory = config.DATA_STORAGE_DIR
    ensure_download_dir(directory)
    run_test_queue()
