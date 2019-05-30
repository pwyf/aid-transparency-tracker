Aid Transparency Tracker
========================

A data quality measurement tool for international aid data.


Setup
-----

Run the following commands to bootstrap your environment ::

    git clone https://github.com/pwyf/aid-transparency-tracker
    cd aid-transparency-tracker
    git submodule init
    git submodule update
    pipenv sync
    cp .env.example .env
    npm install
    npm run-script build

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration ::

    pipenv run flask db upgrade

Create a new superuser with ::

    pipenv run flask createsuperuser

Next you need to seed the database. Organisations can be imported to the database from CSV ::

    pipenv run flask setup orgs [import_data/example_organisations.csv]

    pipenv run flask setup components import_data/2018_components.csv
    pipenv run flask setup indicators import_data/2018_indicators.csv

IATI data can then be downloaded, imported and tested for all organisations ::

    pipenv run flask iati download
    pipenv run flask iati import
    pipenv run flask iati test

To run the webpack dev server and flask server concurrently, run ::

    npm start

Deployment
----------

To deploy::

    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export DATABASE_URL="<YOUR DATABASE URL>"
    npm run build   # build assets with webpack
    pipenv run flask run       # start the flask server

In your production environment, make sure the ``FLASK_DEBUG`` environment
variable is unset or is set to ``0``.


Shell
-----

To open the interactive shell, run ::

    pipenv run flask shell

By default, you will have access to the flask ``app``.


Running Tests
-------------

To run all tests, run ::

    pipenv run flask test


Migrations
----------

Whenever a database migration needs to be made. Run the following commands ::

    pipenv run flask db migrate

This will generate a new migration script. Then run ::

    pipenv run flask db upgrade

To apply the migration.

For a full migration command reference, run ``flask db --help``.


Asset Management
----------------

Files placed inside the ``assets`` directory and its subdirectories
(excluding ``js`` and ``css``) will be copied by webpack's
``file-loader`` into the ``static/build`` directory, with hashes of
their contents appended to their names.  For instance, if you have the
file ``assets/img/favicon.ico``, this will get copied into something
like
``static/build/img/favicon.fec40b1d14528bf9179da3b6b78079ad.ico``.
You can then put this line into your header::

    <link rel="shortcut icon" href="{{asset_url_for('img/favicon.ico') }}">

to refer to it inside your HTML page.  If all of your static files are
managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in your ``settings.py``::

    SEND_FILE_MAX_AGE_DEFAULT = 31556926  # one year
