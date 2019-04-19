import csv

from flask.cli import with_appcontext
import click

from . import models


@click.command()
@click.argument('input', type=click.File('r'))
@with_appcontext
def import_orgs(input):
    '''Import a CSV of organisation data.'''
    reader = csv.DictReader(input)
    data = [x for x in reader]
    for row in data:
        org = models.Organisation.where(slug=row['slug']).first()
        if org:
            org.update(**row)
        else:
            models.Organisation.create(**row)
