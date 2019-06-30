# Aid Transparency Tracker

IATI Data Quality measurement tool

## Installation

Clone the relevant branch of this repo:

    git clone --recursive --branch original-version https://github.com/pwyf/aid-transparency-tracker.git
    cd aid-transparency-tracker

Set up a virtualenv:

    virtualenv ./pyenv

Append the following to your virtualenv activate script:

    export FLASK_APP=iatidataquality/__init__.py

E.g. with:

    echo "export FLASK_APP=iatidataquality/__init__.py" >> pyenv/bin/activate

Activate the virtualenv:

    source ./pyenv/bin/activate

Install the requirements:

    pip install -r requirements.txt

Copy and edit the config.py.tmpl:

    cp config.py.tmpl config.py

Run the setup script to populate the database:

    flask setup

This will prompt you to create a new admin user.

## Running

You can run a development server with:

    flask run

## Survey component

The survey component currently requires the existence of three files (could be abstracted in future). Move them from the tests directory to the DATA_STORAGE_DIR you specified in config.py. E.g., if you set the directory to be /home/me/data/:

    cp tests/2012_2013_organisation_mapping.csv /home/me/data/
    cp tests/2012_indicators.csv /home/me/data/
    cp tests/2012_results.csv /home/me/data/

## Reinitialise

You can drop all tables with:

    flask drop_db

Then follow the installation instructions to get reinitialise.

## Updating sampling poisoning

    bin/dqtool update-sampling

