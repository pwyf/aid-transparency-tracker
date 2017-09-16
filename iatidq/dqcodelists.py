
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from collections import defaultdict

import requests
import unicodecsv

from iatidataquality import app, db
from . import models


CODELIST_API = app.config["CODELIST_API"]

def generateCodelists():
    codelists = db.session.query(models.CodelistCode.code,
                     models.Codelist.name
                    ).join(models.Codelist).all()
    cl = defaultdict(list)
    for code, codelist in codelists:
        cl[codelist].append(code)
    return dict(cl)

def generateACodelist(codelist_name):
    codelist = db.session.query(models.CodelistCode.name, 
                                models.CodelistCode.code
            ).filter(models.Codelist.name==codelist_name
            ).join(models.Codelist).all()
    return codelist

def reformatCodelist(codelist_name):
    codelist = generateACodelist(codelist_name)
    return dict(map(lambda x: (x.code, x.name), codelist))

def handle_row(codelist, codelist_url, crow):
    codelistcode = models.CodelistCode.query.filter_by(
        code=crow['code'], codelist_id=codelist.id).first()

    if not codelistcode:
        codelistcode = models.CodelistCode()
    codelistcode.setup(
        name = crow.get('name', ''),
        code = crow['code'],
        codelist_id = codelist.id
        )
    codelistcode.source = codelist_url
    db.session.add(codelistcode)

def add_manual_codelist(filename, codelist_name, codelist_description):
    f = open(filename)
    codelist_data = unicodecsv.DictReader(f)
    
    with db.session.begin():
        codelist = models.Codelist.query.filter(
            models.Codelist.name==codelist_name).first()

        if not codelist:
            codelist = models.Codelist()
        codelist.setup(
            name = codelist_name,
            description = codelist_description
            )
        codelist.source = filename
        db.session.add(codelist)

    with db.session.begin():
       [ handle_row(codelist, filename, crow) for crow in codelist_data ]

def handle_codelist(codelists_url, codelist_name):
    codelist_url = '{}json/en/{}.json'.format(CODELIST_API, codelist_name)
    print(codelist_url)

    codelist_data = requests.get(codelist_url).json()

    with db.session.begin():
        codelist = models.Codelist.query.filter(
            models.Codelist.name==codelist_name).first()

        if not codelist:
            codelist = models.Codelist()
        codelist.setup(
            name=codelist_name,
            description=codelist_data['metadata']['description']
        )
        codelist.source = codelists_url
        db.session.add(codelist)

    with db.session.begin():
        [handle_row(codelist, codelist_url, crow) for crow in codelist_data['data']]

def importCodelists():
    codelists_url = (CODELIST_API + 'codelists.json')

    codelists_data = requests.get(codelists_url).json()

    for codelist_name in codelists_data:
        handle_codelist(codelists_url, codelist_name)

    print "Imported successfully"
    return True

if __name__ == "__main__":
    importCodelists()
