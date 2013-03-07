#!/usr/bin/env python

# this line must precede ckan import
import config

from iatidataquality.util import ensure_download_dir
from iatidataquality.download_queue import run_download_queue

if __name__ == '__main__':
    print "Starting up..."
    directory = config.DATA_STORAGE_DIR
    ensure_download_dir(directory)
    run_download_queue()

