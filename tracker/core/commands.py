import csv

from flask.cli import with_appcontext
import click

from . import models


@click.group('setup')
def setup_cli():
    """Various setup commands."""
    pass


@setup_cli.command('orgs')
@click.argument('input', type=click.File('r'))
@with_appcontext
def import_orgs(input):
    """Import a CSV of organisation data."""
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
            click.echo(f'Updating {org.name} ({org.slug}) ...')
            org.update(**row)
        else:
            click.echo(f'Creating {row["name"]} ({row["slug"]}) ...')
            org = models.Organisation.create(**row)
        org.session.commit()
