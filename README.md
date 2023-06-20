# Aid Transparency Tracker

A data quality measurement tool for international aid data.

## Installation

**N.B. If you would like to develop locally with vagrant follow these [instructions](./vagrant-readme.md)**

Run the following commands to bootstrap your environment:

``` bash
git clone --recursive https://github.com/pwyf/aid-transparency-tracker.git
cd aid-transparency-tracker
```

Setup a virtual environment, and install dependencies:

``` bash
    python3 -m venv .ve
    echo "export FLASK_APP=iatidataquality/__init__.py" >> .ve/bin/activate
    source .ve/bin/activate
    pip install "setuptools<58"
    pip install -r requirements.txt
```

Copy and edit the config.py.tmpl, including pointing at a postgres database:

``` bash
cp config.py.tmpl config.py
```

Finally, run the setup script to populate your database:

``` bash
flask setup
```

This will prompt you to create a new admin user.

## Fetching and testing data

1. You can download a dump of today’s IATI data with:
    ``` bash
    flask download_data
    ```
   The data will be downloaded to the __iatikitcache__ directory by default, or you can add an iatikit.ini file to specify a different location.

2. The relevant data (according to the organisations in your database) should then be moved into place using:
    ``` bash
    flask import_data
    ```
   This will move files into the `IATI_DATA_PATH` specified in your config.py

3. Tests are run on this data using:
    ``` bash
    flask test_data
    ```
   The complete output of this is stored as CSV files in the `IATI_RESULT_PATH` specified in your config.py

4. Finally, you can refresh the aggregate data shown in the tracker using:
    ``` bash
    flask aggregate_results
    ```
   This step will destructively populate the `aggregateresult` table of your database.

## Running

You can run a development server with:
``` bash
flask run
```
## Survey component

The survey component currently requires the existence of three files (could be abstracted in future). Move them from the tests directory to the DATA_STORAGE_DIR you specified in config.py. E.g., if you set the directory to be /home/me/data/:

``` bash
cp tests/2012_2013_organisation_mapping.csv /home/me/data/
cp tests/2012_indicators.csv /home/me/data/
cp tests/2012_results.csv /home/me/data/
```

## Reinitialise

If at any time you need to reset, you can drop all tables using:

``` bash
flask drop_db
```
Then follow the installation instructions to reinitialise.
