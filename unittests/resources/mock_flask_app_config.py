from os.path import abspath, dirname, join, realpath


SQLALCHEMY_TRACK_MODIFICATIONS = False
#SQLALCHEMY_DATABASE_URI = 'mysql+oursql://user:passwd@127.0.0.1/iatidq'
#SQLALCHEMY_DATABASE_URI = 'sqlite:///dataquality.sqlite'
#SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2:///iatidq'
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://postgres:dcf5636196aa409b75a0f7a73a314df4c8fc05d9b9fc0cad9b87ee64f2d6d2b1@127.0.0.1:5433/iatidq'
DATABASE_INFO = {
    'database': 'iatidq'
}
SAMPLING_DB_FILENAME = join(realpath(dirname(__file__)), 'sample_work.db')

SECRET_KEY = "YOUR-REALLY-SECRET-KEY"

INDICATOR_GROUP = u"2024index"

CODELIST_API = u"https://reference.iatistandard.org/{version}/codelists/downloads/clv2"

ORG_FREQUENCY_API_URL = "http://publishingstats.iatistandard.org/timeliness_frequency.csv"
IATIUPDATES_URL = "http://tracker.publishwhatyoufund.org/iatiupdates/api/package/hash/"

# if this is set to False, don't be surprised if your database
# becomes ludicrously huge. Heed my words.
REMOVE_RESULTS = True

INTRO_HTML = ''
# INTRO_HTML = 'Data collection for the <a href="http://www.publishwhatyoufund.org/the-index/">2020 Aid Transparency Index</a> has now started. We will release more detailed information in April 2020 when the Aid Transparency Index will be launched. Results and analysis for previous years is available in the <a href="http://ati.publishwhatyoufund.org/" target="_blank">2018 Index</a>.'

ATI_YEAR = '2024'
PREVIOUS_ATI_YEAR = '2022'

basedir = dirname(abspath(__file__))
IATI_DATA_PATH = join(basedir, 'data')
IATI_RESULT_PATH = join(basedir, 'results')

APP_ADMIN_USERNAME = "localdev"
APP_ADMIN_PASSWORD = "localdev"
