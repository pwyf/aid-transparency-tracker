import csv

from flask.cli import with_appcontext
import click

from . import models


@click.group('setup')
def setup_cli():
    """Various setup commands."""
    pass


@setup_cli.command('orgs_file')
@click.argument('input', type=click.File('r'))
@with_appcontext
def import_orgs(orgs_file):
    """Import a CSV of organisation data."""
    reader = csv.DictReader(orgs_file)
    data = [{
        'name': row['name'],
        'id': row['id'],
        'registry_slug': (row['registry_slug']
                          if row['registry_slug']
                          else None),
        'test_condition': (row['test_condition']
                           if row['test_condition']
                           else None),
    } for row in reader]
    for row in data:
        org = models.Organisation.find(row['id'])
        if org:
            click.echo(f'Updating {org.name} ({org.id}) ...')
            org.update(**row)
        else:
            click.echo(f'Creating {row["name"]} ({row["id"]}) ...')
            org = models.Organisation.create(**row)
        org.session.commit()


@setup_cli.command('components')
@click.argument('component_file', type=click.File('r'))
@with_appcontext
def import_components(component_file):
    """Import a CSV of component data."""
    reader = csv.DictReader(component_file)
    for row in reader:
        component = models.Component.find(row['id'])
        if component:
            click.echo(f'Updating {component.name} ({component.id}) ...')
            component.update(**row)
        else:
            click.echo(f'Creating {row["name"]} ({row["id"]}) ...')
            component = models.Component.create(**row)
        component.session.commit()


@setup_cli.command('indicators')
@click.argument('indicator_file', type=click.File('r'))
@with_appcontext
def import_indicators(indicator_file):
    """Import a CSV of indicator data."""
    reader = csv.DictReader(indicator_file)
    data = [{
        'id': row['id'],
        'name': row['name'],
        'indicator_type': row['indicator_type'],
        'component_id': row['component_id'],
        'description': row['description'],
        'order': int(row['order']),
        'ordinal': False if row['ordinal'] == '0' else True,
        'weight': row['weight'],
        'has_format': False if row['has_format'] == '0' else True,
    } for row in reader]
    for row in data:
        indicator = models.Indicator.find(row['id'])
        if indicator:
            click.echo(f'Updating {indicator.name} ({indicator.id}) ...')
            indicator.update(**row)
        else:
            click.echo(f'Creating {row["name"]} ({row["id"]}) ...')
            indicator = models.Indicator.create(**row)
        indicator.session.commit()
