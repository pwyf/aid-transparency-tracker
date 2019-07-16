from os.path import exists, join, isdir
from os import listdir, makedirs, unlink
import shutil

import click
import iatikit

from . import app, db
from iatidq import dqimporttests, dqindicators, dqorganisations, dqusers
from iatidq import setup as dqsetup
from iatidq.models import Organisation, Test
from iatidq.sample_work import sample_work, db as sample_work_db
from beta import utils, infotest


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    dqimporttests.hardcodedTests()


@app.cli.command()
def drop_db():
    """Drop all tables."""
    click.secho('\nWarning! This will drop all database tables!', fg='red')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    click.echo('DB dropped.')


@app.cli.command()
def setup():
    """
    Quick setup. Will init db, add tests, add codelists,
    add indicators, refresh package data from Registry
    """
    click.secho('\nWarning! This is a potentially destructive operation!',
                fg='red')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    dqsetup.setup()


@app.cli.command()
@click.option('--username', prompt='Username')
@click.password_option()
def create_admin(username, password):
    """Create an admin user."""
    dqsetup.setup_admin_user(username, password)


@app.cli.command()
def update_frequency():
    """Update frequency of publication from IATI dashboard"""
    dqorganisations.downloadOrganisationFrequency()


@app.cli.command()
@click.option('--filename', help='Set filename of data to test')
def import_indicators(filename):
    """Import indicators. Will try to assign indicators to existing tests."""
    indicator_group_name = app.config['INDICATOR_GROUP']
    if filename:
        dqindicators.importIndicatorsFromFile(indicator_group_name, filename)
    else:
        dqindicators.importIndicators()


@app.cli.command()
@click.option('--filename', required=True, help='Set filename of data to test')
def import_organisations(filename):
    """
    Import organisations. Will try to create and assign
    organisations to existing packages.
    """
    dqorganisations.importOrganisationPackagesFromFile(filename)


@app.cli.command()
@click.option('--filename', required=True,
              help='Set filename of users to import')
def import_users(filename):
    """Import users and permissions."""
    dqusers.importUserDataFromFile(filename)


@app.cli.command()
@click.option('--date', default='latest',
              help='Date of the data to test, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
@click.option("--filename")
@click.option("--org-ids")
@click.option("--test-ids")
def setup_sampling(date, filename, org_ids, test_ids):
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
            click.secho('Error: No IATI results to sample.', fg='red', err=True)
        click.echo('Perhaps you need to run tests, using:', err=True)
        click.echo('\n    $ flask test_data ' +
                   '--date {}\n'.format(date), err=True)
        raise click.Abort()

    if not filename:
        filename = app.config['SAMPLING_DB_FILENAME']
    if exists(filename):
        click.secho('Warning: Sample database exists.', fg='red')
        click.confirm('Delete and continue?', abort=True)
        unlink(filename)

    if org_ids:
        org_ids = map(int, org_ids.split(","))
        orgs = [Organisation.find(id_) for id_ in org_ids]
    else:
        orgs = Organisation.all()

    if test_ids:
        test_ids = map(int, test_ids.split(","))
        tests = [Test.find(id_) for id_ in test_ids]
    else:
        tests = sample_work.all_tests()

    sample_work_db.make_db(filename, orgs, tests, snapshot_date)


@app.cli.command()
def download_data():
    """Download a snapshot of all IATI data."""
    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    iatikit.download.data()


@app.cli.command()
def import_data():
    """Import the relevant data from the downloaded IATI snapshot."""
    updated_on = iatikit.data().last_updated.date()
    input_path = iatikit.data().path
    output_path = join(app.config.get('IATI_DATA_PATH'), str(updated_on))

    click.echo('Copying files into place ...')
    click.echo('Output path: {output_path}'.format(output_path=output_path))

    if exists(output_path):
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


@app.cli.command()
@click.option('--date', default='latest',
              help='Date of the data to test, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
@click.option('--refresh/--no-refresh', default=True,
              help='Refresh schema and codelists.')
def test_data(date, refresh):
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

    if exists(root_output_path):
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
    for publisher in publishers:
        org = Organisation.where(registry_slug=publisher.name.decode()).first()
        if not org:
            click.secho('Error: Publisher "{}" '.format(publisher.name) +
                        'not found in database. Database and XML ' +
                        'may be out of sync.',
                        fg='red', err=True)
            raise click.Abort()
        click.echo('\nTesting organisation: {name} ({slug}) ...'.format(
            name=org.organisation_name, slug=org.registry_slug
        ))
        output_path = join(root_output_path, org.registry_slug)
        makedirs(output_path)
        for test in all_tests:
            output_filepath = join(output_path,
                                   utils.slugify(test.name) + '.csv')
            click.echo(test)
            utils.run_test(test, publisher, output_filepath,
                           None, codelists=codelists,
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
            org, snapshot_date, test_name, current_data_results)


@app.cli.command()
@click.option('--date', default='latest',
              help='Date of the data to summarize, in YYYY-MM-DD. ' +
                   'Defaults to most recent.')
def aggregate_results(date):
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
        for registry_slug in publishers:
            org = Organisation.where(
                registry_slug=registry_slug.decode()).first()
            if not org:
                click.secho('Error: Publisher '
                            '"{}" '.format(registry_slug) +
                            'not found in database. Database and XML ' +
                            'may be out of sync.',
                            fg='red', err=True)
                raise click.Abort()
            utils.summarize_results(org, snapshot_result_path, all_tests)

            current_data_results = utils.load_current_data_results(
                org, snapshot_result_path)
            utils.summarize_results(
                org, snapshot_result_path, all_tests, current_data_results)
