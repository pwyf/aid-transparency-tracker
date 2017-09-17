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
