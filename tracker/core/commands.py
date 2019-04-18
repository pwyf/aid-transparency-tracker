import csv

from flask.cli import with_appcontext
import click

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
