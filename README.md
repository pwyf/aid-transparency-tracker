IATI-Data-Quality
=================

IATI Data Quality measurement

Set up a virtualenv:
virtualenv ./pyenv

Activate the virtualenv:
source ./pyenv/bin/activate

Install the requirements:
pip install -r requirements.txt

Copy and edit the config.py.tmpl:
cp config.py.tmpl config.py

Run the celery script:
======================

python manage.py celeryd

Run the server:
===============

python manage.py runserver
