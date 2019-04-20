from os.path import dirname, exists, join
import shutil

from flask import current_app
from flask.cli import with_appcontext
import click
import iatikit

from ..core import models


@click.group('iati')
def iati_cli():
    """Automated test commands."""
    pass


@iati_cli.command('download')
@with_appcontext
def download_iati_data():
    '''Fetch the relevant data from the IATI registry.'''

    if models.Organisation.query.count() == 0:
        click.echo('Error: No organisations to fetch data for.')
        click.echo('Perhaps you need to import some, using:')
        click.echo('\n    $ flask setup orgs\n')
        raise click.Abort()

    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    iatikit.download.data()
    updated_on = iatikit.data().last_updated.date()

    input_path = join(iatikit.data().path, 'data')
    output_path = join(current_app.config.get('IATI_DATA_PATH'), str(updated_on))

    click.echo('Copying files into place ...')
    click.echo(f'Output path: {output_path}')

    if exists(output_path):
        click.echo('Error: Output path exists.')
        raise click.Abort()

    for organisation in models.Organisation.query:
        if not organisation.registry_slug:
            # if the org isn’t an IATI publisher, skip
            continue
        # Copy files into place
        shutil.copytree(join(input_path, organisation.registry_slug),
                        join(output_path, organisation.slug))
