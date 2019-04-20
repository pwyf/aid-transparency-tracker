from os import listdir, makedirs
from os.path import exists, join
import shutil

from flask import current_app
from flask.cli import with_appcontext
import click
import iatikit

from ..core import models
from . import utils


@click.group('iati')
def iati_cli():
    """Automated test commands."""
    pass


@iati_cli.command('download')
@with_appcontext
def download_iati_data():
    '''Fetch the relevant data from the IATI registry.'''

    if models.Organisation.query.count() == 0:
        click.secho('Error: No organisations to fetch data for.', fg='red')
        click.echo('Perhaps you need to import some, using:')
        click.echo('\n    $ flask setup orgs\n')
        raise click.Abort()

    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    iatikit.download.data()
    updated_on = iatikit.data().last_updated.date()

    input_path = iatikit.data().path
    output_path = join(current_app.config.get('IATI_DATA_PATH'), str(updated_on))

    click.echo('Copying files into place ...')
    click.echo(f'Output path: {output_path}')

    if exists(output_path):
        click.secho('Error: Output path exists.', fg='red')
        raise click.Abort()
    makedirs(output_path)

    shutil.copy(join(input_path, 'metadata.json'),
                join(output_path, 'metadata.json'))

    for organisation in models.Organisation.query:
        if not organisation.registry_slug:
            # if the org isn’t an IATI publisher, skip
            continue
        # Copy data files into place
        shutil.copytree(join(input_path, 'data', organisation.registry_slug),
                        join(output_path, 'data', organisation.slug))
        # Copy metadata files into place
        shutil.copytree(join(input_path, 'metadata', organisation.registry_slug),
                        join(output_path, 'metadata', organisation.slug))


@iati_cli.command('test')
@click.option('--date', default='latest', help='Date of the data to test, in ' +
                                               'YYYY-MM-DD. Defaults to ' +
                                               'most recent.')
@with_appcontext
def run_iati_tests(date):
    '''Test a set of downloaded IATI data.'''

    click.echo('Loading tests ...')
    all_tests = utils.load_tests()

    iati_data_path = current_app.config.get('IATI_DATA_PATH')
    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    try:
        snapshot_dates = listdir(join(iati_data_path))
        if snapshot_dates == []:
            raise FileNotFoundError

        if date == 'latest':
            snapshot_date = max(snapshot_dates)
        else:
            if not exists(join(iati_data_path, date)):
                raise ValueError
            snapshot_date = date
    except FileNotFoundError:
        click.secho('Error: No IATI data to test.', fg='red')
        click.echo('Perhaps you need to download some, using:')
        click.echo('\n    $ flask iati download\n')
        raise click.Abort()
    except ValueError:
        click.secho(f'Error: No IATI data found for given date ({date}).', fg='red')
        raise click.Abort()

    click.echo(f'Testing IATI data snapshot ({snapshot_date}) ...')
    data_path = join(iati_data_path, snapshot_date)
    output_path = join(iati_result_path, snapshot_date)

    publishers = iatikit.data(path=data_path).publishers
    for publisher in publishers:
        org = models.Organisation.where(slug=publisher.name).first()
        click.echo(f'Testing organisation: {org.name} ({org.slug}) ...')
        path = join(output_path, org.slug)
        makedirs(path, exist_ok=True)
        for test in all_tests:
            fname = join(path, utils.slugify(test.name) + '.csv')
            click.echo(f'{test} ...')
            utils.run_test(test, publisher, fname)
