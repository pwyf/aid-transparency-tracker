#!/usr/bin/env python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2014  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

# this line must precede ckan import
import config
from iatidq.test_queue import test_queue_once
from iatidq.util import ensure_download_dir

if __name__ == '__main__':
    directory = config.DATA_STORAGE_DIR
    ensure_download_dir(directory)
    test_queue_once()
