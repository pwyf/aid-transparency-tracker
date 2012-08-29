IATI-Data-Quality
=================

IATI Data Quality measurement tool

License: AGPL v3.0
==================

Copyright (C) 2012

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


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

In a production environment:
============================

Run fcgi.py

... or for testing:
===================

Run testrun.py
