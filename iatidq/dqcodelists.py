
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import models
import unicodecsv
from collections import defaultdict

import util

CODELIST_API = "http://data.aidinfolabs.org/data/%s"

def generateCodelists():
    codelists = db.session.query(models.CodelistCode.code,
                     models.Codelist.name
                    ).join(models.Codelist).all()
    cl = defaultdict(list)
    for code, codelist in codelists:
        cl[codelist].append(code)
    return dict(cl)

def importCodelists(filename=False, local=False):
    codelists_url = (CODELIST_API % ("codelist.csv"))

    f = util.stream_of_file(codelists_url, local)
    if not f:
        return False

    codelists_data = unicodecsv.DictReader(f)

    for row in codelists_data:
        codelist = models.Codelist.query.filter(models.Codelist.name==row['name']).first()
        if not codelist:
            codelist = models.Codelist()
        codelist.setup(
            name = row['name'],
            description = row['description']
            )
        codelist.source = codelists_url
        db.session.add(codelist)
        db.session.commit()
        
        codelist_url = (CODELIST_API % ("codelist/" + row['name'] + ".csv"))
        f = util.stream_of_file(codelist_url, local)
        if not f:
            return False
        codelist_data = unicodecsv.DictReader(f)
        for crow in codelist_data:
            codelistcode = models.CodelistCode.query.filter_by(code=crow['code'], codelist_id=codelist.id).first()
            if not codelistcode:
                codelistcode = models.CodelistCode()
            codelistcode.setup(
                name = crow['name'],
                code = crow['code'],
                codelist_id = codelist.id
                )
            codelistcode.source = codelist_url
            db.session.add(codelistcode)
    db.session.commit()
    print "Imported successfully"
    return True

if __name__ == "__main__":
    importCodelists()
