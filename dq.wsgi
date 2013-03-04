#!/usr/bin/env python
import logging, sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/usr/sites/IATI-Data-Quality/pyenv/lib/python2.7/site-packages')
sys.path.insert(0, '/usr/sites/IATI-Data-Quality')
from iatidataquality import app as application
