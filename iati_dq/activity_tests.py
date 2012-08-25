# provide variables from xpath API

def test_check_date(activity):
    thedate = activity.find('activity-date').get('iso-date')
    if (thedate is None):
	    return False
    else:
        return True

def test_title(activity):
    thetitle = activity.find('title').text
    
    if (thetitle is None):
	    return False
    else:
        return True

def test_title_size(activity):
    thetitle = activity.find('title').text
    if ((thetitle is not None) and (len(thetitle)>20)):
	    return True
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)
