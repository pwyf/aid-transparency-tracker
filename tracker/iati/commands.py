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
        click.echo('No organisations to fetch data for.')
        raise click.Abort()

    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    iatikit.download.data()
    updated_on = iatikit.data()._last_updated.date()

    base_path = join(dirname(current_app.root_path))
    input_path = join(base_path, '__iatikitcache__', 'registry', 'data')
    output_path = join(base_path, 'org_xml', str(updated_on))

    if exists(output_path):
        click.echo('Output path exists – aborting.')
        raise click.Abort()

    click.echo('Fetching a snapshot of *all* data from the IATI registry ...')
    for organisation in models.Organisation.query:
        if not organisation.registry_slug:
            # if the org isn’t an IATI publisher, skip
            continue
        # Copy files into place
        shutil.copytree(join(input_path, organisation.registry_slug),
                        join(output_path, organisation.slug))
