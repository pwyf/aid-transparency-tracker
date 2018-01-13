from os.path import join

import click

from . import app, db
from iatidq import dqcodelists, dqdownload, dqfunctions, dqimporttests, dqindicators, dqminimal, dqorganisations, dqprocessing, dqregistry, dqruntests, dqusers, queue
from iatidq import setup as dqsetup
from iatidq.models import Organisation
from iatidq.sample_work import sample_work, db as sample_work_db


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    dqimporttests.hardcodedTests()


@app.cli.command()
def drop_db():
    """Drop the database."""
    click.echo('\nWarning! This will drop all database tables!')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    click.echo('DB dropped.')


@app.cli.command()
@click.option('--minimal', is_flag=True, help='Operate on a minimal set of packages')
def setup(minimal):
    """
    Quick setup. Will init db, add tests, add codelists,
    add indicators, refresh package data from Registry
    """
    dqsetup.setup(minimal)


@app.cli.command()
@click.option('--username', prompt='Username')
@click.password_option()
def create_admin(username, password):
    """Create an admin user."""
    dqsetup.setup_admin_user(username, password)


@app.cli.command()
@click.option('--filename', required=True, help='Set filename of data to test')
@click.option('--level', type=int, default=1, help='Test level (e.g. 1 == Activity)')
def enroll_tests(filename, level):
    """Enroll a CSV file of tests."""
    result = dqimporttests.importTestsFromFile(
        filename=filename.decode(),
        level=level
    )
    if not result:
        print('Error importing')


@app.cli.command()
def clear_revisionid():
    """Clear CKAN revision ids"""
    dqfunctions.clear_revisions()


@app.cli.command()
def import_codelists():
    """Import codelists"""
    dqcodelists.importCodelists()


@app.cli.command()
def import_basic_countries():
    """Import basic list of countries"""
    filename = 'tests/countries_basic.csv'
    codelist_name = 'countriesbasic'
    codelist_description = 'Basic list of countries for running tests against'
    dqcodelists.add_manual_codelist(filename, codelist_name, codelist_description)


@app.cli.command()
@click.option('--minimal', is_flag=True, help='Operate on a minimal set of packages')
@click.option('--matching', help='Regular expression for matching packages')
def download_packages(minimal, matching):
    """Download packages"""
    if minimal:
        for package_name, _ in dqminimal.which_packages:
            dqdownload.run(package_name=package_name)
    elif matching:
        for pkg_name in dqregistry.matching_packages(matching):
            dqdownload.run(package_name=pkg_name)
    else:
        dqdownload.run()


@app.cli.command()
def update_frequency():
    """Update frequency"""
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
@click.option('--package-name', required=True, help='Set name of package to be tested')
@click.option('--filename', required=True, help='Set filename of data to test')
def enqueue_test(package_name, filename):
    """Set a package to be tested"""
    dqruntests.enqueue_package_for_test(filename, package_name)


@app.cli.command()
@click.option('--package-name', help='Set name of package to be tested')
@click.option('--minimal', is_flag=True, help='Operate on a minimal set of packages')
@click.option('--matching', help='Regular expression for matching packages')
def refresh_packages(package_name, minimal, matching):
    """Refresh packages"""
    pkg_names = None
    if package_name:
        pkg_names = [package_name]
    elif minimal:
        pkg_names = [i[0] for i in dqminimal.which_packages]
    elif matching:
        pkg_names = [i for i in dqregistry.matching_packages(matching)]

    if pkg_names is not None:
        for name in pkg_names:
            dqregistry.refresh_package_by_name(name)
    else:
        dqregistry.refresh_packages()


@app.cli.command()
@click.option('--matching', required=True, help='Regular expression for matching packages')
def activate_packages(matching):
    """Mark all packages as active"""
    matching_packages = [(i, True) for i in dqregistry.matching_packages(matching)]
    dqregistry.activate_packages(matching_packages, clear_revision_id=True)


@app.cli.command()
def create_aggregation_types():
    """Create basic aggregation types."""
    dqsetup.create_aggregation_types()


@app.cli.command()
@click.option('--runtime-id', required=True, type=int, help='Runtime ID')
@click.option('--package-id', required=True, type=int, help='Package ID')
def aggregate_results(runtime_id, package_id):
    """Trigger result aggregation"""
    dqprocessing.aggregate_results(runtime_id, package_id)


@app.cli.command()
def create_inforesult_types():
    """Create basic infroresult types."""
    dqsetup.create_inforesult_types()


@app.cli.command()
def setup_organisations():
    """Setup organisations."""
    dqsetup.setup_organisations()


@app.cli.command()
@click.option('--filename', required=True, help='Set filename of data to test')
def setup_users(filename):
    """Setup users and permissions."""
    dqusers.importUserDataFromFile(filename)


@app.cli.command()
def clear_queues():
    queue_names = ['iati_download_queue', 'iati_tests_queue']
    for queue_name in queue_names:
        queue.delete_queue(queue_name)


@app.cli.command()
@click.option('--organisation-code', required=True, help='Code of organisation to test')
def test_packages(organisation_code):
    """Test packages for a given organisation"""
    sql = '''
        select package_name from organisation
            left join organisationpackage on organisation.id = organisation_id
            left join package on package_id = package.id
            where organisation_code = %s and active = 't';
    '''
    results = db.engine.execute(sql, (organisation_code,))
    package_names = [row[0] for row in results.fetchall()]

    for package_name in package_names:
        dirname = app.config.get('DATA_STORAGE_DIR')
        filename = join(dirname, '{}.xml'.format(package_name))
        from iatidq import test_queue
        test_queue.test_one_package(filename, package_name)


@app.cli.command()
@click.option("--filename")
@click.option("--org-ids")
@click.option("--test-ids")
@click.option("--update", is_flag=True)
def setup_sampling(filename, org_ids, test_ids, update):
    if not filename:
        filename = app.config['SAMPLING_DB_FILENAME']

    if org_ids:
        org_ids = map(int, org_ids.split(","))
    else:
        org_ids = [org.id for org in Organisation.all()]

    if test_ids:
        test_ids = map(int, test_ids.split(","))
    else:
        test_ids = sample_work.all_test_ids()

    create = not update

    print("test ids: {}".format(test_ids))
    sample_work_db.make_db(filename, org_ids, test_ids, create)
