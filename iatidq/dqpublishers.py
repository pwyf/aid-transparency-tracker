
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models
import csv
import util
import unicodecsv



def importPublisherPackagesFromFile(filename, publisher_c=None, publisher_n=None):
    with file(filename) as fh:
        return _importPublisherPackages(publisher_c, publisher_n, fh, True)

def _importPublisherPackages(publisher_c, publisher_n, fh, local):

        data = unicodecsv.DictReader(fh)

        for row in data:
            if publisher_c is None:
                checkP = publishers(row['publisher_code'])
                publisher_code = row['publisher_code']
                publisher_name = row['publisher_name']
            else:
                checkP = publishers(publisher_c)
                publisher_code = publisher_c
                publisher_name = publisher_n
            if checkP:
                publisher = checkP
            else:
                publisher = addPublisher({"publisher_name": publisher_name,
                                          "publisher_code": publisher_code
                                        })
            print publisher_code
            packages = models.Package.query.filter(models.PackageGroup.publisher_iati_id==publisher_code
                        ).join(models.PackageGroup
                        ).all()

            if not packages:
                continue
            else:
                for package in packages:
                    publisherpackage = addPublisherPackage({
                                "publisher_id" : publisher.id,
                                "package_id" : package.id
                            })
                
        print "Imported successfully"
        return True

def publishers(publisher_code=None):
    if publisher_code is None:
        publishers = models.Publisher.query.all()
    else:
        publishers = models.Publisher.query.filter_by(publisher_code=publisher_code).first()
    return publishers

def publisherPackages(publisher_code=None):
    if publisher_code is not None:
        publisherpackages = db.session.query(models.Package,
                                             models.PublisherPackage
                        ).filter(models.Publisher.publisher_code==publisher_code
                        ).join(models.PublisherPackage
                        ).join(models.Publisher
                        ).all()
        return publisherpackages
    else:
        return False

def addPublisher(data):
    checkP = models.Publisher.query.filter_by(publisher_code=data["publisher_code"]).first()
    if not checkP:
        newP = models.Publisher()
        newP.setup(
            publisher_name = data["publisher_name"],
            publisher_code = data["publisher_code"]
        )
        db.session.add(newP)
        db.session.commit()
        return newP
    else:
        return False

def updatePublisher(publisher_code, data):
    checkP = models.Publisher.query.filter_by(publisher_code=publisher_code).first()
    if (checkP is not None):
        checkP.publisher_code = data["publisher_code"]
        checkP.publisher_name = data["publisher_code"]
        db.session.add(checkP)
        db.session.commit()
        return checkP
    else:
        return False

def addPublisherPackage(data):
    checkPP=models.PublisherPackage.query.filter_by(publisher_id=data['publisher_id'], package_id=data['package_id']
                ).first()
    if (checkPP is None):
        newPP = models.PublisherPackage()
        newPP.setup(
            publisher_id = data["publisher_id"],
            package_id = data["package_id"]
        )
        db.session.add(newPP)
        db.session.commit()
        return newPP
    else:
        return False

def deletePublisherPackage(publisher_code, package_name, publisherpackage_id):
    checkPP = models.PublisherPackage.query.filter_by(id=publisherpackage_id).first()
    if checkPP:
        db.session.delete(checkPP)
        db.session.commit()
        return checkPP
    else:
        return False
