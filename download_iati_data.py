#!/usr/bin/env python
from iatidataquality import models, db, DATA_STORAGE_DIR, dqdownload

if __name__ == '__main__':
    print """

         ## Fetch packages from IATI Registry ##

         NB, you need to run iatidataquality/quickstart.py 
         before running this script in order to populate the 
         list of packages
          """
    dqdownload.run()
