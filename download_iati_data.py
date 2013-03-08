#!/usr/bin/env python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import dqdownload

if __name__ == '__main__':
    print """

         ## Fetch packages from IATI Registry ##

         NB, you need to run quickstart.py 
         before running this script in order to populate the 
         list of packages
          """
    dqdownload.run()
