"""Automated test views."""
from flask import Blueprint


def get_blueprint(app):
    return Blueprint('iati', __name__, url_prefix='/xml',
                     static_folder=app.config.get('IATI_DATA_PATH'),
                     static_url_path='')
