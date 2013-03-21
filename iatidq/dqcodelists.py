
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
import urllib2
import lxml.etree

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

def handle_row(codelist, crow):
    #print crow
    codelistcode = models.CodelistCode.query.filter_by(
        code=crow['code'], codelist_id=codelist.id).first()

    if not codelistcode:
        codelistcode = models.CodelistCode()
    codelistcode.setup(
        name = crow['name'],
        code = crow['code'],
        codelist_id = codelist.id
        )
    codelistcode.source = codelist_url
    db.session.add(codelistcode)

def handle_codelist(codelists_url, row):
    codelist = models.Codelist.query.filter(
        models.Codelist.name==row['name']).first()

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
    print row
    print
    print codelist_url
    print

    f = urllib2.urlopen(codelist_url)
    codelist_data = unicodecsv.DictReader(f)

    [ handle_row(codelist, crow) for crow in codelist_data ]

def pretend_xml_is_csv(f):
    data = f.read()
    root = lxml.etree.XML(data)
    
    for elt in root.findall('codelist'):
        yield {
            "name": elt.find('name').text,
            "description":elt.find('description').text
            }

def importCodelists():
    codelists_url = (CODELIST_API % ("codelist.xml"))

    f = urllib2.urlopen(codelists_url)

    codelists_data = pretend_xml_is_csv(f)

    [ handle_codelist(codelists_url, row) for row in codelists_data ]

    db.session.commit()
    print "Imported successfully"
    return True

if __name__ == "__main__":
    importCodelists()
