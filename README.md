# Aid Transparency Tracker

A data quality measurement tool for international aid data.

## Installation

Run the following commands to bootstrap your environment:

    git clone --recursive --branch original-version https://github.com/pwyf/aid-transparency-tracker.git
    cd aid-transparency-tracker

Setup a virtual environment, and install dependencies:

    virtualenv pyenv
    echo "export FLASK_APP=iatidataquality/__init__.py" >> pyenv/bin/activate
    source pyenv/bin/activate
    pip install -r requirements.txt

Set the FLASK_APP environment variable:

    export FLASK_APP=iatidataquality/__init__.py
    echo "export FLASK_APP=iatidataquality/__init__.py" >> pyenv/bin/activate

Copy and edit the config.py.tmpl, including pointing at a postgres database:

    cp config.py.tmpl config.py

Finally, run the setup script to populate your database:

    flask setup

This will prompt you to create a new admin user.

## Fetching and testing data

1. You can download a dump of today’s IATI data with:

       flask download_data

   The data will be downloaded to the __iatikitcache__ directory by default, or you can add an iatikit.ini file to specify a different location.

2. The relevant data (according to the organisations in your database) should then be moved into place using:

       flask import_data

   This will move files into the `IATI_DATA_PATH` specified in your config.py

3. Tests are run on this data using:

       flask test_data

   The complete output of this is stored as CSV files in the `IATI_RESULT_PATH` specified in your config.py

4. Finally, you can refresh the aggregate data shown in the tracker using:

       flask aggregate_results

   This step will destructively populate the `aggregateresult` table of your database.

## Running

You can run a development server with:

    flask run

## Survey component

The survey component currently requires the existence of three files (could be abstracted in future). Move them from the tests directory to the DATA_STORAGE_DIR you specified in config.py. E.g., if you set the directory to be /home/me/data/:

    cp tests/2012_2013_organisation_mapping.csv /home/me/data/
    cp tests/2012_indicators.csv /home/me/data/
    cp tests/2012_results.csv /home/me/data/

## Reinitialise

If at any time you need to reset, you can drop all tables using:

    flask drop_db

Then follow the installation instructions to reinitialise.

----

## Updating sampling poisoning

    bin/dqtool update-sampling
