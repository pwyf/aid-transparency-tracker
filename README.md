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

Run the celery script:

    python manage.py celeryd

Run the server:

    python manage.py runserver

Import Scripts
==============

These steps must be followed in this order, and you must have created the database tables (`manage.py runserver` does this automatically).

Import the tests to the database, run the server and go to (e.g.):

    http://127.0.0.1:5000/tests/import/

Provide the password and click "Import tests"

Download IATI data
==================

Currently moving out of using Celery. The new process will be:

1) Refresh all Packages from IATI Registry (via a nice UI + background process)
2) Set "active" to True for some packages (via a nice UI)
3) Check for all Packages where CKAN's revision_id is different from the Package's package_revision_id.

You can do 1) and 2) automatically by running:

    python quickstart.py

Then run 3) to update all CKAN metadata and download the file:

    python download_iati_data.py

In order for 3) to work, you need to have RabbitMQ running on your system (if you have Celery you should be fine) and then run:

    python download_backend.py

Run tests
=========

There are two ways to run tests (remember, you need Celery running via `python manage.py celeryd`):

1) via the browser

    http://127.0.0.1/tests/runtests

2) via the command line

    cd iatidataquality
    python dqruntests.py
