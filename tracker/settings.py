"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from os.path import abspath, dirname, join

from environs import Env


basedir = dirname(abspath(__file__))

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SQLALCHEMY_DATABASE_URI = env.str('DATABASE_URL', default='sqlite:////' +
                                  join(basedir, 'db.sqlite3'))
SECRET_KEY = env.str('SECRET_KEY')
BCRYPT_LOG_ROUNDS = env.int('BCRYPT_LOG_ROUNDS', default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
WEBPACK_MANIFEST_PATH = 'webpack/manifest.json'

SECURITY_PASSWORD_SALT = SECRET_KEY
SECURITY_TRACKABLE = True
SECURITY_USER_IDENTITY_ATTRIBUTES = 'username'

IATI_DATA_PATH = join(dirname(basedir), 'org_xml')
