from os.path import exists, join, isdir
from os import listdir, makedirs
import shutil

import click
import iatikit

from . import app, db
from iatidq import dqcodelists, dqfunctions, dqimporttests, dqindicators, dqminimal, dqorganisations, dqprocessing, dqregistry, dqusers
from iatidq import setup as dqsetup
from iatidq.models import Organisation
from iatidq.sample_work import sample_work, db as sample_work_db
from beta import utils


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    dqimporttests.hardcodedTests()


@app.cli.command()
def drop_db():
    """Drop all tables."""
    click.echo('\nWarning! This will drop all database tables!')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    click.echo('DB dropped.')


@app.cli.command()
def setup():
    """
    Quick setup. Will init db, add tests, add codelists,
    add indicators, refresh package data from Registry
    """
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
def create_inforesult_types():
    """Create basic inforesult types."""
    dqsetup.create_inforesult_types()


@app.cli.command()
def setup_organisations():
    """Setup organisations."""
    dqsetup.setup_organisations()


@app.cli.command()
@click.option('--filename', required=True, help='Set filename of users to import')
def setup_users(filename):
    """Setup users and permissions."""
    dqusers.importUserDataFromFile(filename)


@app.cli.command()
@click.option("--filename")
@click.option("--org-ids")
@click.option("--test-ids")
@click.option("--create", is_flag=True)
def setup_sampling(filename, org_ids, test_ids, create):
    if not filename:
        filename = app.config['SAMPLING_DB_FILENAME']

    if org_ids:
        org_ids = map(int, org_ids.split(","))
    else:
        org_ids = [org.id for org in Organisation.all()]

    if test_ids:
        test_ids = map(int, test_ids.split(","))
    else:
        all_tests = sample_work.all_tests()
        test_ids = [x.id for x in all_tests]

    print("test ids: {}".format(test_ids))
    sample_work_db.make_db(filename, org_ids, test_ids, create)


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
        click.secho('Error: Output path exists.', fg='red', err=True)
        raise click.Abort()
    makedirs(output_path)

    shutil.copy(join(input_path, 'metadata.json'),
                join(output_path, 'metadata.json'))

    with click.progressbar(Organisation.all()) as all_organisations:
        for organisation in all_organisations:
            if not organisation.registry_slug:
                continue
            # Copy data files into place
            shutil.copytree(join(input_path, 'data', organisation.registry_slug),
                            join(output_path, 'data', organisation.registry_slug))
            # Copy metadata files into place
            shutil.copytree(join(input_path, 'metadata', organisation.registry_slug),
                            join(output_path, 'metadata', organisation.registry_slug))


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

    if exists(root_output_path):
        click.secho('Error: Output path exists.', fg='red', err=True)
        raise click.Abort()

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
        org = Organisation.where(registry_slug=publisher.name).first()
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
            click.secho('Error: No IATI results to summarize.', fg='red', err=True)
        click.echo('Perhaps you need to run tests, using:', err=True)
        click.echo('\n    $ flask test_data ' +
                   '--date {}\n'.format(date), err=True)
        raise click.Abort()

    with db.session.begin():
        db.session.execute('''truncate aggregateresult''')

    click.echo('Loading tests ...')
    all_tests = utils.load_tests()

    snapshot_result_path = join(iati_result_path, result_date)

    click.echo('Summarizing results from IATI data snapshot ' +
               '({}) ...'.format(result_date))
    publishers = [x for x in listdir(snapshot_result_path)
                  if isdir(join(snapshot_result_path, x))]
    for registry_slug in publishers:
        org = Organisation.where(registry_slug=unicode(registry_slug)).first()
        if not org:
            click.secho('Error: Publisher '
                        '"{}" '.format(registry_slug) +
                        'not found in database. Database and XML ' +
                        'may be out of sync.',
                        fg='red', err=True)
            raise click.Abort()
        click.echo('Summarizing results for organisation: ' +
                   '{} ({}) ...'.format(
                    org.organisation_name, org.registry_slug))
        utils.summarize_results(org, snapshot_result_path, all_tests)

        current_data_results = utils.load_current_data_results(org, snapshot_result_path)
        utils.summarize_results(org, snapshot_result_path, all_tests, current_data_results)
