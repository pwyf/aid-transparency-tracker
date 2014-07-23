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

You need RabbitMQ running for the tests processing to work. It's probably sensible to configure that before starting.

Set up a virtualenv:

    virtualenv ./pyenv

Activate the virtualenv:

    source ./pyenv/bin/activate

Install the requirements:

    pip install -r requirements.txt

Copy and edit the config.py.tmpl:

    cp config.py.tmpl config.py

Run the setup script to populate the database (append ` --minimal` if you want to try it out with just a few packages):

    python quickstart.py --setup

This will also create a default username and password; please create a new user and then delete the default one!

Run the server:

    python manage.py runserver

To get the download data and the tests running, run the backends (more details below):

    python download_backend.py
    python tests_backend.py

You can also use `supervisor`:

1. Rename the provided `supervisord.conf.tmpl` file to `supervisord.conf`, and ensure it matches your paths (especially the path to your virtualenv)
2. Run `supervisord -n` (Remove `-n` if you don't want to see the output, but it's probably useful for testing)


Choose packages for activation
==============================

From the web interface, log in and from the top-right drop-down menu, click `manage packages`. Select the packages you want to activate and click `activate packages`. Then, you can click the drop-down menu again and choose `run tests`.

Remember, you need the download and tests backends working for this, which you could do directly with `./download_backend.py` or through supervisor.

Survey component 
================

The survey component currently requires the existence of three files (could be abstracted in future). Move them from the tests directory to the DATA_STORAGE_DIR you specified in config.py. E.g., if you set the directory to be /home/me/data/:
    
    cp tests/2012_2013_organisation_mapping.csv /home/me/data/
    cp tests/2012_indicators.csv /home/me/data/
    cp tests/2012_results.csv /home/me/data/

Reinitialise
============

    python quickstart.py --drop-db
    python quickstart.py --init-db
    python quickstart.py --setup --minimal
    python quickstart.py --refresh --minimal
    bin/dqtool --mode=reload-packages --organisation=GB-1
    python download_once.py
    python tests_once.py

Run unit tests
==============

FIXME

Run aggregation test
====================

    bin/dqtool --mode compare-aggregation --organisation GB-1 --filename unittests/artefacts/json/dfid-sample-aggregation-data.json

This runs an aggregation on the packages for organisation GB-1 and compares
the results with the stashed file in unittests/artefacts/json/dfid-sample-aggregation-data.json; if the results are different, then a new file is output

Reload a package
================

    bin/dqtool --mode reload-package --name dfid-tz

Adding new tests
================

    ./quickstart.py --enroll-tests --filename tests/some-new-file.csv

You will then need to associate each test with an indicator:

    bin/dqtool --mode associate-test --test-id 52 --indicator conditions


Checking if tests are complete
==============================

    bin/dqtool --mode check-package-results --all --organisation GB-1


Updating sampling poisoning
===========================

    bin/dqtool --mode update-sampling

