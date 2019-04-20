"""Automated test views."""
from flask import Blueprint


blueprint = Blueprint('iati', __name__, url_prefix='/xml', static_folder='../../org_xml', static_url_path='')
