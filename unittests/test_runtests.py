def test_checktitle():
    import models
    test = models.Test()
    test.name = "title/text() exists?"
    test.active = True
    test.description = "Does title exist?"
    test.test_group = "title"
    test.test_level=1
    db.session.add(test)
    db.session.commit()
    print "Wrote to DB, ID is",test.id

    from iatidataquality.dqparsetests import test_functions as tf
    test_functions = tf()
    print test_functions[test.id](etree.parse("testxml.xml").find('iati-activity'))
