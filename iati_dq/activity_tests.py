# provide variables from xpath API

def activity_date_iso_date_exists(activity):
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

def description_exists(activity):
    """
    Description exists
    """
    thedescription = activity.find('description').text
    if (thedescription is None):
        return False
    else:
        return True

def description_greater_than_40_characters(activity):
    """
    Description is greater than 40 characters
    """
    thedescription = activity.find('description').text
    if ((thedescription is not None) and (len(thedescription)>40)):
	    return True
    else:
        return False

if __name__ == "__main__":
    app.run(debug=True)
