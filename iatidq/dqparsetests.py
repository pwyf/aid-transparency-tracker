
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import iatidq.models as models
import foxpath

from iatidq import db

def get_active_tests():
    for test in models.Test.query.filter(models.Test.active == True).all():
        yield test

def test_functions():
    try:
        return foxpath.generate_test_functions(get_active_tests())
    finally:
        db.session.commit()
