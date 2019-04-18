from os.path import join
import shutil
import csv

from flask.cli import with_appcontext
import click
import iatikit

from . import models


@click.command()
@click.argument('input', type=click.File('r'))
@with_appcontext
def import_orgs(input):
    reader = csv.DictReader(input)
    data = [x for x in reader]
    for row in data:
        models.Organisation.create(
            name=row['Name'],
            org_id=row['Org ID'],
            registry_handle=row['Registry ID'],
        )


@click.command()
@with_appcontext
def download_iati_data():
    '''Fetch a snapshot of all IATI data from the registry.'''
    # iatikit.download.data()
    updated_on = iatikit.data()._last_updated.date()

    input_path = join('__iatikitcache__', 'registry', 'data')
    output_path = join('tracker', 'static', 'xml', str(updated_on))

    for organisation in models.Organisation.query:
        # TODO: Move files into place
        shutil.move(join(input_path, organisation.registry_handle),
                    join(output_path, organisation.registry_handle))
    shutil.rmtree('__iatikitcache__')
