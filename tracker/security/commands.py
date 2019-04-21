from flask.cli import with_appcontext
import click
from sqlalchemy.exc import IntegrityError

from ..extensions import security


@click.command()
@with_appcontext
def createsuperuser():
    """Create a new superuser."""
    username = click.prompt('Username')
    email = click.prompt('Email address', default='')
    password = click.prompt('Password', hide_input=True)
    confirm_password = click.prompt('Password again', hide_input=True)
    if password != confirm_password:
        click.secho('Error: Passwords did not match.', fg='red', err=True)
        raise click.Abort()
    try:
        user = security.datastore.create_user(
            username=username,
            email=email,
            password=password)
        role = security.datastore.find_or_create_role('super')
        security.datastore.add_role_to_user(user, role)
        security.datastore.commit()
        click.echo('Superuser created.')
    except IntegrityError as e:
        click.secho(f'Error: There was a problem creating the superuser.',
                    fg='red', err=True)
