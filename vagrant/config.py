from os.path import abspath, dirname, join, realpath


BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "/"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2:///vagrant'
DATABASE_INFO = {
    'database': 'vagrant'
}

DATA_STORAGE_DIR = join(realpath(dirname(__file__)), 'dq', 'data')
SAMPLING_DB_FILENAME = join(realpath(dirname(__file__)), 'dq', 'sample_work', 'sample_work.db')

SECRET_KEY = "secret"

INDICATOR_GROUP = u"2018index"

CODELIST_API = u"https://reference.iatistandard.org/{version}/codelists/downloads/clv2"

SETUP_ORGS = ['dfid', 'fco', 'beis', 'dhsc', 'defra_transparency', 'dwp', 'ukmod']

# SETUP_PKG_COUNTER = 10

ORG_FREQUENCY_API_URL = "http://publishingstats.iatistandard.org/timeliness_frequency.csv"
IATIUPDATES_URL = "http://2018tracker.publishwhatyoufund.org/iatiupdates/api/package/hash/"

REMOVE_RESULTS = True

INTRO_HTML = ''
# INTRO_HTML = 'Data collection for the <a href="http://www.publishwhatyoufund.org/the-index/">2018 Aid Transparency Index</a> has now started. We will release more detailed information in June 2018 when the Aid Transparency Index will be launched. Results and analysis for previous years is available in the <a href="http://ati.publishwhatyoufund.org/" target="_blank">2016 Index</a>.'

ATI_YEAR = "2019"
PREVIOUS_ATI_YEAR = "2018"

basedir = dirname(abspath(__file__))
IATI_DATA_PATH = join(basedir, 'dq', 'data')
IATI_RESULT_PATH = join(basedir, 'dq', 'results')

