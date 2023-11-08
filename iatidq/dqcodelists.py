
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from collections import defaultdict

import requests
import csv

from iatidataquality import app, db
from . import models


def generateCodelists():
    codelists = db.session.query(
        models.CodelistCode.code,
        models.Codelist.name
    ).join(models.Codelist).all()

    cl = defaultdict(list)
    for code, codelist in codelists:
        cl[codelist].append(code)
    return dict(cl)


def generateACodelist(codelist_name):
    codelist = db.session.query(
        models.CodelistCode.name,
        models.CodelistCode.code
    ).filter(
        models.Codelist.name == codelist_name
    ).join(models.Codelist).all()
    return codelist


def reformatCodelist(codelist_name):
    codelist = generateACodelist(codelist_name)
    return dict([(x.code, x.name) for x in codelist])


def handle_row(codelist, codelist_url, crow):
    codelistcode = models.CodelistCode.query.filter_by(
        code=crow['code'], codelist_id=codelist.id).first()

    if not codelistcode:
        codelistcode = models.CodelistCode()
    codelistcode.setup(
        name=crow.get('name', ''),
        code=crow['code'],
        codelist_id=codelist.id
    )
    codelistcode.source = codelist_url
    db.session.add(codelistcode)


def add_manual_codelist(filename, codelist_name, codelist_description):
    f = open(filename)
    codelist_data = csv.DictReader(f)

    with db.session.begin():
        codelist = models.Codelist.query.filter(
            models.Codelist.name == codelist_name).first()

        if not codelist:
            codelist = models.Codelist()
        codelist.setup(
            name=codelist_name,
            description=codelist_description
            )
        codelist.source = filename
        db.session.add(codelist)

    with db.session.begin():
        for crow in codelist_data:
            handle_row(codelist, filename, crow)


def handle_codelist(codelists_url, codelist_url, codelist_name):
    print(codelist_url)

    codelist_data = requests.get(codelist_url).json()
    if codelist_data['attributes']['complete'] != '1':
        # we don't care about incomplete codelists,
        # because we can't check against them anyway
        return

    with db.session.begin():
        codelist = models.Codelist.query.filter(
            models.Codelist.name == codelist_name).first()

        if not codelist:
            codelist = models.Codelist()
        codelist.setup(
            name=codelist_name,
            description=codelist_data['metadata']['description']
        )
        codelist.source = codelists_url
        db.session.add(codelist)

    with db.session.begin():
        for crow in codelist_data['data']:
            handle_row(codelist, codelist_url, crow)


def importCodelists():
    tmpl_prefix = app.config["CODELIST_API"]

    mapping_tmpl = tmpl_prefix + '/mapping.json'
    codelist_tmpl = tmpl_prefix + '/json/en/{codelist_name}.json'
    versions = ('1.05', '2.03',)

    for version in versions:
        version = version.replace('.', '')
        codelists_url = mapping_tmpl.format(version=version)
        mapping = requests.get(codelists_url).json()
        codelist_names = list({x['codelist']: None for x in mapping}.keys())
        for codelist_name in codelist_names:
            codelist_url = codelist_tmpl.format(
                version=version, codelist_name=codelist_name)
            handle_codelist(codelists_url, codelist_url, codelist_name)
    print("Imported successfully")
    return True


if __name__ == "__main__":
    importCodelists()
