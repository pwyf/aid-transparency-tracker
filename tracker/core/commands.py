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
    data = [{
        'name': row['name'],
        'slug': row['slug'],
        'registry_slug': row['registry_slug'] if row['registry_slug'] else None,
        'test_condition': row['test_condition'] if row['test_condition'] else None,
    } for row in reader]
    for row in data:
        org = models.Organisation.where(slug=row['slug']).first()
        if org:
            org.update(**row)
        else:
            models.Organisation.create(**row)
