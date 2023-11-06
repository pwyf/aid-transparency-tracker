# Aid Transparency Tracker

A data quality measurement tool for international aid data.

## Installation

**N.B. If you would like to develop locally with vagrant follow these [instructions](./vagrant/vagrant-readme.md)**

Run the following commands to bootstrap your environment:

``` bash
git clone --recursive https://github.com/pwyf/aid-transparency-tracker.git
cd aid-transparency-tracker
```

Setup a virtual environment, and install dependencies:

``` bash
python3 -m venv .ve
source .ve/bin/activate
pip install "setuptools<58"
pip install -r requirements.txt
```

Install and run a postgres database. If you have docker-compose, you can do this:

```
docker-compose -f docker-compose-postgres.yml up -d
```

(You may need to run `docker compose` instead of `docker-compose` if you have docker v2 installed).

You can login to the PostgreSQL server (which might be useful to check things are working) using `psql` with the following command (using password from dockerfile; or using port and password you set, if not using the docker compose setup):

```commandline
psql -h localhost -p 5433 -U postgres
```


Copy and if necessary edit the config.py.tmpl. (If you installed postgres using docker-compose you shouldn't need to edit anything.)

``` bash
cp config.py.tmpl config.py
```

If you're running this for the first time, edit `tests/organisations_with_identifiers.csv` to have less organisations. e.g. For just one:

```
cp tests/organisations_with_identifiers_sample_1_org.csv tests/organisations_with_identifiers.csv
```

Finally, run the setup script to populate your database:

``` bash
flask setup
```

This will prompt you to create a new admin user (this will be the username & password you use to login to the ATT web app, once it is up and running--see 'Running' section below).

## Fetching and testing data

1. You can download a dump of today’s IATI data with:
    ``` bash
    flask download_data
    ```
   The data will be downloaded to the `__iatikitcache__` directory by default, or you can add an `iatikit.ini` file to specify a different location.


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


## Reinitialise

If at any time you need to reset, you can drop all tables using:

``` bash
flask drop_db
```
Then follow the installation instructions to reinitialise.

## Code formatting

We are currently incrementally adding files to black and isort code formatting.

To ensure the relevant files are formatted correctly, run:

```
black conftest.py config_test.py unittests/test_web.py integration_tests/
isort conftest.py config_test.py unittests/test_web.py integration_tests/
```

These will be checked by GitHub Actions.

## Data files required by the tests

The PWYF tests which assess the quality of the data use various files which are stored
in the `tests/` folder. Some of these files need to be updated from the following
locations:

**`orgid.json`**: http://org-id.guide/download.json

**`publishers.json`**: https://iatiregistry.org/publisher/download/json

**`CRSChannelCode.json`**: https://iatistandard.org/en/iati-standard/203/codelists/crschannelcode/




