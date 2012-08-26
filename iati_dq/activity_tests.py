# provide variables from xpath API

def activity_date_exists(activity):
    """
    Activity Date ISO date exists
    """
    # Should also check whether it's in the format YYYY-MM-DD
    thedate = activity.find('activity-date').get('iso-date')
    if (thedate is None):
        return False
    else:
        return True

def title_exists(activity):
    """
    Title exists
    """
    thetitle = activity.find('title').text
    if (thetitle is None):
        return False
    else:
        return True

def title_greater_than_10_characters(activity):
    """
    Title is greater than 10 characters
    """
    thetitle = activity.find('title').text
    if ((thetitle is not None) and (len(thetitle)>10)):
	    return True
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)
