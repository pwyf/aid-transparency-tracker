""" This script is to quickly get started with this tool, by:
        1) creating DB
        2) populating the list of packages from the Registry (will download basic data about all packages)
        3) setting 3 to "active"
"""
from iatidataquality.db import *
from iatidataquality import models, dqregistry

db.create_all()

def run():
    which_packages = [
                ('worldbank-tz', True),
                ('unops-tz', True),
                ('dfid-tz', True)
                ]
    dqregistry.refresh_packages()
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

if __name__ == '__main__':
    run()
