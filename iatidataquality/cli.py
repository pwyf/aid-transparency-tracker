import click

from . import app, db
from iatidq import dqimporttests
from iatidq import setup as dqsetup


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    dqimporttests.hardcodedTests()

@app.cli.command()
def drop_db():
    """Drop the database."""
    click.echo('\nWarning! This will drop all database tables!')
    click.confirm('Are you really really sure?', abort=True)
    db.drop_all()
    click.echo('DB dropped.')

@app.cli.command()
@click.option('--minimal', is_flag=True, help='Operate on a minimal set of packages')
def setup(minimal):
    """
    Quick setup. Will init db, add tests, add codelists,
    add indicators, refresh package data from Registry
    """
    dqsetup.setup(minimal)

@app.cli.command()
@click.option('--username', prompt='Username')
@click.password_option()
def create_admin(username, password):
    """Create an admin user."""
    dqsetup.setup_admin_user(username, password)
