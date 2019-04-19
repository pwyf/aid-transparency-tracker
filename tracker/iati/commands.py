from os.path import exists, join
import shutil

from flask.cli import with_appcontext
import click
import iatikit

from ..core import models


@click.command()
@with_appcontext
def download_iati_data():
    '''Fetch the relevant IATI data from the registry.'''

    # Fetch a snapshot of *all* IATI data from the registry
    iatikit.download.data()
    updated_on = iatikit.data()._last_updated.date()

    input_path = join('__iatikitcache__', 'registry', 'data')
    output_path = join('tracker', 'static', 'xml', str(updated_on))

    if exists(output_path):
        click.echo('Output path exists – aborting.')
        raise click.Abort()

    for organisation in models.Organisation.query:
        if not organisation.registry_slug:
            # if the org isn’t an IATI publisher, skip
            continue
        # Copy files into place
        shutil.copytree(join(input_path, organisation.registry_slug),
                        join(output_path, organisation.slug))
