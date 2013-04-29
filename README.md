IATI-Data-Quality
=================

IATI Data Quality measurement tool

License: AGPL v3.0
==================

Copyright (C) 2012

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Installation
============

Set up a virtualenv:

    virtualenv ./pyenv

Activate the virtualenv:

    source ./pyenv/bin/activate

Install the requirements:

    pip install -r requirements.txt

Copy and edit the config.py.tmpl:

    cp config.py.tmpl config.py

Run the server:

    python manage.py runserver

To get the download data and the tests running, run the backends (more details below):

    python download_backend.py
    python tests_backend.py

Import Scripts
==============

If you're having problems with creation of database tables then just run:

    python manage.py runserver

Import the tests to the database: run the server and go to (e.g.):

    http://127.0.0.1:5000/tests/import/

Provide the password and click "Import tests"

Download IATI data
==================

This can now be accessed from the UI, or else from the command line

1. Refresh all Packages from IATI Registry (via a nice UI + background process)
2. Set "active" to True for some packages (via a nice UI)
3. Check for all Packages where CKAN's revision_id is different from the Package's package_revision_id.

You can do 1) and 2) automatically by running:

    python quickstart.py

    or via the browser interface, go to "Refresh from Registry"

Then run 3) to update all CKAN metadata and download the file:

    python download_iati_data.py

    or via the  browser interface, go to "Download from Registry"

In order for 3) to work, you need to have RabbitMQ running on your system and then run:

    python download_backend.py

You can also use `supervisor`:

1. Rename the provided `supervisord.conf.tmpl` file to `supervisord.conf` to match your paths (especially the path to your virtualenv)
2. Run `supervisord -n` (Remove `-n` if you don't want to see the output, but it's probably useful for testing)

Run tests
=========

There are two ways to run tests:

1. via the browser

    http://127.0.0.1:5000/runtests

2. via the command line

    python run_tests.py

For either, make sure you have the backend running:

    python tests_backend.py

Survey component 
================

The survey component currently requires the existence of three files (could be abstracted in future). Move them from the tests directory to the DATA_STORAGE_DIR you specified in config.py. E.g., if you set the directory to be /home/me/data/:
    
    cp tests/2012_2013_organisation_mapping.csv /home/me/data/
    cp tests/2012_indicators.csv /home/me/data/
    cp tests/2012_results.csv /home/me/data/
