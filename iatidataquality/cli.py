from os.path import dirname, exists, join, isdir
from os import listdir, makedirs
from sqlite3 import dbapi2 as sample_work_sqlite
import shutil

import click
import iatikit
import csv

from . import app, db
from iatidq import dqcodelists, dqimporttests, dqindicators, dqorganisations, dqusers
from iatidq import setup as dqsetup
from iatidq.models import Organisation, Test, OrganisationCondition
from iatidq.sample_work import sample_work, db as sample_work_db
from beta import utils, infotest


@app.cli.command("init_db")
def init_db():
    """Initialize the database."""
    db.create_all()
    dqimporttests.hardcodedTests()


@app.cli.command("drop_db")
def drop_db():
    """Drop all tables."""
    click.secho('\nWarning! This will drop all database tables!', fg='red')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    click.echo('DB tables dropped.')


@app.cli.command()
@click.option('--force', is_flag=True, default=False,
              help='Skip the "This is potentially destructive" confirmation prompt')
@click.option('--admin-from-config', is_flag=True, default=False,
              help='Automatically create admin user from config file. Avoids interactive prompts')
def setup(force, admin_from_config):
    """
    Quick setup. Will init db, add tests, add codelists,
    add indicators, refresh package data from Registry
    """
    if force:
        click.echo('\nSkipping confirmation as --force is set')
    else:
        click.secho('\nWarning! This is a potentially destructive operation!',
                    fg='red')
        click.confirm('Are you really really sure?', abort=True)

    db.drop_all()
    dqsetup.setup(admin_from_config)


@app.cli.command("create_admin")
@click.option('--username', prompt='Username')
@click.password_option()
def create_admin(username, password):
    """Create an admin user."""
    dqsetup.setup_admin_user(username, password)


@app.cli.command("import_codelists")
def import_codelists():
    """Import IATI codelists from the IATI reference API."""
    dqcodelists.importCodelists()


@app.cli.command("update_frequency")
def update_frequency():
    """Update frequency of publication from IATI dashboard"""
    dqorganisations.downloadOrganisationFrequency()


@app.cli.command("import_indicators")
@click.option('--filename', help='Set filename of data to test')
def import_indicators(filename):
    """Import indicators. Will try to assign indicators to existing tests."""
    indicator_group_name = app.config['INDICATOR_GROUP']
    if filename:
        dqindicators.importIndicatorsFromFile(indicator_group_name, filename)
    else:
        dqindicators.importIndicators()


@app.cli.command("import_indicator_descriptions")
def import_indicator_descriptions():
    dqindicators.importIndicatorDescriptionsFromFile(
        app.config["INDICATOR_GROUP"],
        "tests/indicators.csv")

@app.cli.command("import_tests")
@click.option('--filename', default="tests/tests.yaml", help="Import the test definitions from file")
def import_tests(filename):
    """Import test definitions"""
    dqimporttests.importTestsFromFile(filename, 1)


@app.cli.command("import_organisations")
@click.option('--filename', required=True, help='Set filename of data to test')
def import_organisations(filename):
    """
    Import organisations. Will try to create and assign
    organisations to existing packages.
    """
    dqorganisations.importOrganisationPackagesFromFile(filename)


@app.cli.command("import_users")
@click.option('--filename', required=True,
              help='Set filename of users to import')
def import_users(filename):
    """Import users and permissions."""
    dqusers.importUserDataFromFile(filename)


@app.cli.command("setup_sampling")
@click.option('--date', default='latest',
              help='Date of the data to test, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
@click.option("--filename")
@click.option("--org-ids")
@click.option("--test-ids")
@click.option("--round-name", default=None,
              help='Name for the new sampling round (defaults to "Round N")')
@click.option('--replace-latest', is_flag=True, default=False,
              help='Delete and recreate the most recent sampling round ' +
                   '(including its reviewer responses) instead of ' +
                   'creating a new one')
@click.option('--force', is_flag=True, default=False,
              help='Skip the "This is potentially destructive" confirmation prompt')
def setup_sampling(date, filename, org_ids, test_ids, round_name, replace_latest, force):
    """Generate the sampling database (Environment variable PWYF_SAMPLE_SIZE can be used to set the number of samples per test)"""
    iati_result_path = app.config.get('IATI_RESULT_PATH')
    try:
        snapshot_dates = listdir(join(iati_result_path))
        if date == 'latest':
            snapshot_date = max(snapshot_dates)
        else:
            if not exists(join(iati_result_path, date)):
                raise ValueError
            snapshot_date = date
    except ValueError:
        if date:
            click.secho('Error: No IATI results found for given date ' +
                        '({}).'.format(date),
                        fg='red', err=True)
        else:
            click.secho('Error: No IATI results to sample.',
                        fg='red', err=True)
        click.echo('Perhaps you need to run tests, using:', err=True)
        click.echo('\n    $ flask test_data ' +
                   '--date {}\n'.format(date), err=True)
        raise click.Abort()

    if not filename:
        filename = app.config['SAMPLING_DB_FILENAME']

    if replace_latest:
        click.secho('Warning: This will delete and recreate the most ' +
                    'recent sampling round, including any reviewer ' +
                    'responses recorded for it.', fg='red')
        if not force:
            click.confirm('Continue?', abort=True)

    if org_ids:
        org_ids = list(map(int, org_ids.split(",")))
        orgs = [Organisation.find(id_) for id_ in org_ids]
    else:
        orgs = [org for org in Organisation.all() if org.registry_slug]

    if test_ids:
        test_ids = list(map(int, test_ids.split(",")))
        tests = [Test.find(id_) for id_ in test_ids]
    else:
        tests = sample_work.all_tests()

    try:
        round_id = sample_work_db.make_db(filename, orgs, tests, snapshot_date,
                                           round_name=round_name,
                                           replace_latest=replace_latest)
    except ValueError as e:
        click.secho('Error: {}'.format(e), fg='red', err=True)
        raise click.Abort()

    database = sample_work_sqlite.connect(filename)
    c = database.cursor()
    c.execute('select name from sampling_round where id = ?;', (round_id,))
    round_name = c.fetchone()[0]
    click.echo('Created sampling round {} ("{}").'.format(round_id, round_name))


@app.cli.command("migrate_sampling_rounds")
def migrate_sampling_rounds():
    """One-off migration: add sampling round support to the sampling_failure table."""

    with db.session.begin():
        db.session.execute('''
            ALTER TABLE sampling_failure
            ADD COLUMN IF NOT EXISTS sampling_round INTEGER NOT NULL DEFAULT 1;
        ''')
        db.session.execute('''
            ALTER TABLE sampling_failure
            ADD COLUMN IF NOT EXISTS failed BOOLEAN NOT NULL DEFAULT TRUE;
        ''')
        db.session.execute('''
            UPDATE sampling_failure SET sampling_round = 1
            WHERE sampling_round IS NULL;
        ''')
        db.session.execute('''
            UPDATE sampling_failure SET failed = TRUE
            WHERE failed IS NULL;
        ''')

        pk_info = db.session.execute('''
            SELECT tc.constraint_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = 'sampling_failure'
              AND tc.constraint_type = 'PRIMARY KEY';
        ''').fetchall()
        pk_columns = set(row[1] for row in pk_info)

        if pk_columns != {'organisation_id', 'test_id', 'sampling_round'}:
            constraint_name = pk_info[0][0]
            db.session.execute(
                'ALTER TABLE sampling_failure DROP CONSTRAINT "{}";'.format(constraint_name))
            db.session.execute('''
                ALTER TABLE sampling_failure
                ADD PRIMARY KEY (organisation_id, test_id, sampling_round);
            ''')

    click.echo('sampling_failure table migrated for sampling rounds.')


@app.cli.command("update_publishers")
def update_publishers():
    """Update tests/publishers.json from the IATI Dashboard API."""
    import json
    import urllib.request

    url = 'https://dashboard.iatistandard.org/api/reporting-orgs/'
    results = []
    while url:
        click.echo(f'Fetching {url} ...')
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
        results.extend(data['results'])
        url = data.get('next')

    test_data_path = join(dirname(app.root_path), 'tests')
    output_path = join(test_data_path, 'publishers.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write('\n')
    click.echo(f'Written {len(results)} publishers to {output_path}')


@app.cli.command("download_data")
def download_data():
    """Download a snapshot of all IATI data."""
    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    iatikit.download.data()


@app.cli.command("import_data")
@click.option('--force', is_flag=True, default=False,
              help='Skip the confirmation prompt if data already exists in destination')
def import_data(force):
    """Import the relevant data from the downloaded IATI snapshot."""
    updated_on = iatikit.data().last_updated.date()
    input_path = iatikit.data().path
    output_path = join(app.config.get('IATI_DATA_PATH'), str(updated_on))

    click.echo('Copying files into place ...')
    click.echo('Output path: {output_path}'.format(output_path=output_path))

    if exists(output_path):
        if force:
            click.secho('Warning: Output path exists. Skipping prompt because --force set', fg='yellow')
        else:
            click.secho('Warning: Output path exists.', fg='red')
            click.confirm('Overwrite and continue?', abort=True)
        shutil.rmtree(output_path)

    makedirs(output_path)

    shutil.copy(join(input_path, 'metadata.json'),
                join(output_path, 'metadata.json'))

    with click.progressbar(Organisation.all()) as all_organisations:
        for organisation in all_organisations:
            if not organisation.registry_slug:
                continue
            if exists(join(output_path, 'data', organisation.registry_slug)):
                continue
            if not exists(join(input_path, 'data', organisation.registry_slug)):
                click.echo(' Org "{}" does not exist in download'.format(organisation.registry_slug))
                continue
            # Copy data files into place
            shutil.copytree(join(input_path, 'data',
                                 organisation.registry_slug),
                            join(output_path, 'data',
                                 organisation.registry_slug))
            # Copy metadata files into place
            shutil.copytree(join(input_path, 'metadata',
                                 organisation.registry_slug),
                            join(output_path, 'metadata',
                                 organisation.registry_slug))


@app.cli.command("test_data")
@click.option('--date', default='latest',
              help='Date of the data to test, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
@click.option('--refresh/--no-refresh', default=True,
              help='Refresh schema and codelists.')
@click.option('--part-count', default=1,
              help='Number of parts to split up testing into')
@click.option('--part', default=1,
              help='Select part to run, between 1 and part-count above')
@click.option('--delete/--no-delete', default=True,
              help='delete output path if it exists already')
@click.option('--orgs', default='',
              help='Comman delimeted list of orgs to check, defaults to all orgs')
@click.option('--force', is_flag=True, default=False,
              help='Skip the confirmation prompt if data already exists in schema and codelist directory')
def test_data(date, refresh, part_count, part, delete, orgs, force):
    """Test a set of imported IATI data."""

    iati_data_path = app.config.get('IATI_DATA_PATH')
    iati_result_path = app.config.get('IATI_RESULT_PATH')
    try:
        snapshot_dates = listdir(join(iati_data_path))
        if date == 'latest':
            snapshot_date = max(snapshot_dates)
        else:
            if not exists(join(iati_data_path, date)):
                raise ValueError
            snapshot_date = date
    except ValueError:
        if date:
            click.secho('Error: No IATI data found for given date ' +
                        '({}).'.format(date),
                        fg='red', err=True)
        else:
            click.secho('Error: No IATI data to test.', fg='red', err=True)
        click.echo('Perhaps you need to download some, using:', err=True)
        click.echo('\n    $ flask download_data\n', err=True)
        raise click.Abort()

    snapshot_xml_path = join(iati_data_path, snapshot_date)
    root_output_path = join(iati_result_path, snapshot_date)

    click.echo('Testing: {}'.format(snapshot_xml_path))
    click.echo('Output path: {}'.format(root_output_path))

    if exists(root_output_path) and delete:
        if force:
            click.secho('Warning: Output path exists. Skipping prompt because --force set', fg='yellow')
        else:
            click.secho('Warning: Output path exists.', fg='red')
            click.confirm('Overwrite and continue?', abort=True)
        shutil.rmtree(root_output_path)

    if refresh:
        click.echo('Downloading latest schemas and codelists ...')
        iatikit.download.standard()
    codelists = iatikit.codelists()

    click.echo('Loading tests ...')
    all_tests = utils.load_tests()
    all_tests.append(utils.load_current_data_test())

    click.echo('Testing IATI data snapshot ' +
               '({}) ...'.format(snapshot_date))
    publishers = iatikit.data(path=snapshot_xml_path).publishers
    name_to_publisher = dict((publisher.name, publisher) for publisher in publishers)

    for org in db.session.query(Organisation).all():
        if org.id % part_count != (part -1):
            continue

        orgs_list = orgs.split(',')

        if orgs and org.organisation_code not in orgs_list:
            continue

        if not org.registry_slug:
            continue
        if org.registry_slug not in name_to_publisher:
            continue
        click.echo('\nTesting organisation: {name} ({slug}) ...'.format(
            name=org.organisation_name, slug=org.registry_slug
        ))
        output_path = join(root_output_path, org.organisation_code)

        shutil.rmtree(output_path, ignore_errors=True)
        makedirs(output_path)

        for test in all_tests:
            output_filepath = join(output_path,
                                   utils.slugify(test.name) + '.csv')
            click.echo(test)
            utils.run_test(test, name_to_publisher[org.registry_slug], output_filepath,
                           org.condition, codelists=codelists,
                           today=snapshot_date)

        current_data_results = utils.load_current_data_results(
            org, root_output_path)

        # run country strategy / MoU test
        test_name = 'Strategy (country/sector) or Memorandum of Understanding'
        click.echo(test_name)
        infotest.country_strategy_or_mou(
            org, snapshot_date, test_name, current_data_results)

        # run disaggregated budget test
        test_name = 'Disaggregated budget'
        click.echo(test_name)
        infotest.disaggregated_budget(
            org, snapshot_date, test_name, current_data_results, org.condition)

        # run Networked Data Part 2: use of standardised refs for participating orgs
        test_name = 'Participating Orgs'
        click.echo(test_name)
        infotest.networked_data_part_2(
            org, snapshot_date, test_name, current_data_results, org.condition)
        
        # run Networked Data Part 3: proportion transactions with receiver name/ref
        test_name = 'Transactions with valid receiver'
        click.echo(test_name)
        infotest.networked_data_part_3(
            org, snapshot_date, test_name, current_data_results)




@app.cli.command("aggregate_results")
@click.option('--date', default='latest',
              help='Date of the data to summarize, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
@click.option('--force', is_flag=True, default=False,
              help='Skip the "This is potentially destructive" confirmation prompt')
def aggregate_results(date, force):
    """Summarize results of IATI data tests."""

    iati_result_path = app.config.get('IATI_RESULT_PATH')
    try:
        result_dates = listdir(join(iati_result_path))
        if date == 'latest':
            result_date = max(result_dates)
        else:
            if not exists(join(iati_result_path, date)):
                raise ValueError
            result_date = date
    except ValueError:
        if date:
            click.secho('Error: No IATI results found for given ' +
                        'date ({}).'.format(date), fg='red', err=True)
        else:
            click.secho('Error: No IATI results to summarize.',
                        fg='red', err=True)
        click.echo('Perhaps you need to run tests, using:', err=True)
        click.echo('\n    $ flask test_data ' +
                   '--date {}\n'.format(date), err=True)
        raise click.Abort()

    if force:
        click.echo('\nSkipping confirmation as --force is set')
    else:
        click.secho('\nWarning! This is a destructive operation!', fg='red')
        click.echo('\nAny existing aggregate data will be deleted ' +
                   'from the database.')
        click.echo('(If you still have the raw results, you can regenerate ' +
                   'old aggregate data by specifying a date.)')
        click.confirm('\nAre you really really sure?', abort=True)

    with db.session.begin():
        db.session.execute('''truncate aggregateresult''')

    click.echo('Loading tests ...')
    all_tests = utils.load_tests()

    snapshot_result_path = join(iati_result_path, result_date)

    click.echo('Summarizing results from IATI data snapshot ' +
               '({}) ...'.format(result_date))
    publishers = [x for x in listdir(snapshot_result_path)
                  if isdir(join(snapshot_result_path, x))]
    with click.progressbar(publishers) as publishers:
        for organisation_code in publishers:
            org = Organisation.where(
                organisation_code=organisation_code).first()
            if not org:
                click.secho('Error: Publisher '
                            '"{}" '.format(organisation_code) +
                            'not found in database. Database and XML ' +
                            'may be out of sync.',
                            fg='red', err=True)
                raise click.Abort()
            utils.summarize_results(org, snapshot_result_path, all_tests)

            current_data_results = utils.load_current_data_results(
                org, snapshot_result_path)
            utils.summarize_results(
                org, snapshot_result_path, all_tests, current_data_results)


@app.cli.command("excluded_conditions")
@click.option('--filepath', '-f', help='path to the CSV file with the list of organisation exclusions.')
def excluded_conditions(filepath):
    """Import all test exclusions based on test group per organisation and hierarchy level"""

    def get_all_test_objects(test_group):
        tests = db.session.query(Test).filter_by(test_group=test_group).all()
        return {test.as_dict()["id"]: test.as_dict()["description"] for test in tests}

    def check_organisations_exist(data):
        click.echo('Checking that all organisations in the CSV exist')
        for row in data:
            organisation_slug = str(row[0].lower())
            org = db.session.query(Organisation).filter_by(
                registry_slug=organisation_slug).first()
            if org is None:
                raise Exception('The organisation "{}" could not be found in the database'.format(
                    organisation_slug))
            else:
                click.echo('Organisation {} exists.'.format(organisation_slug))

    def check_tests_exist(data):
        click.echo('Checking that all test groups in the CSV exist')
        for row in data:
            test_group = str(row[1].lower())
            tests = db.session.query(Test).filter_by(
                test_group=test_group).all()
            if len(tests) == 0:
                raise Exception(
                    'The test group "{}" could not be found in the database'.format(test_group))
            else:
                click.echo('Test group {} exists.'.format(test_group))

    def insert_organisation_conditions(data):
        click.echo('Inserting data into the database where applicable')
        condition = str("activity hierarchy")
        operation = str(0)

        for row in data:
            organisation_slug = str(row[0].lower())
            org = db.session.query(Organisation).filter_by(
                registry_slug=organisation_slug).first()
            organisation_id = org.as_dict()["id"]
            condition_value = str(row[2])

            test_group = str(row[1].lower())
            test_objects = get_all_test_objects(test_group)
            for test_id, test_description in list(test_objects.items()):
                pc = OrganisationCondition.query.filter_by(
                    organisation_id=organisation_id, test_id=test_id,
                    operation=operation, condition=condition,
                    condition_value=condition_value).first()

                with db.session.begin():
                    if (pc is None):
                        pc = OrganisationCondition()

                    pc.organisation_id = organisation_id
                    pc.test_id = test_id
                    pc.operation = operation
                    pc.condition = condition
                    pc.condition_value = condition_value
                    pc.description = test_description
                    pc.file = filepath
                    pc.line = str(0)
                    pc.active = True
                    db.session.add(pc)

    with open(filepath) as fh:
        try:
            csv_file = csv.reader(fh)
            csv_list = list(csv_file)
        except:
            raise Exception("An error occured reading the CSV file.")

        check_organisations_exist(csv_list)
        check_tests_exist(csv_list)

        try:
            insert_organisation_conditions(csv_list)
        except:
            raise Exception(
                "An error occured when inserting the conditions into the database.")
