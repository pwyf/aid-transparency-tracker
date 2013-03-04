def test_unique_identifiers(activities):
    context = activities.findall("//iati-activity//iati-identifier")
    if (context is None):
	return False
    else:
        return True
