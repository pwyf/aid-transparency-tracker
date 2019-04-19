"""The app module, containing the app factory function."""
from flask import Flask, render_template
from flask_security import SQLAlchemyUserDatastore

from . import extensions, commands, core, survey, iati, security
from .security.models import User, Role
from .database import BaseModel


def create_app(config_object='tracker.settings'):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    extensions.cache.init_app(app)
    extensions.db.init_app(app)
    extensions.migrate.init_app(app, extensions.db)
    BaseModel.set_session(extensions.db.session)
    extensions.webpack.init_app(app)
    extensions.debug_toolbar.init_app(app)
    datastore = SQLAlchemyUserDatastore(extensions.db, User, Role)
    extensions.security.init_app(app, datastore)


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(survey.views.blueprint)
    app.register_blueprint(core.views.blueprint)


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': extensions.db,
            'Organisation': core.models.Organisation,
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(core.commands.setup_cli)
    app.cli.add_command(iati.commands.iati_cli)
    app.cli.add_command(security.commands.createsuperuser)
