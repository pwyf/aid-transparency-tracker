Feature: Sub-national location

  Scenario Outline: Location (sub-national)
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `recipient-region/@code` is not 998
     and `sector/@code` is not 91010
     then `location` should be present

  Scenario Outline: Location (sub-national) coordinates or point
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `recipient-region/@code` is not 998
     then either `location/coordinates` or `location/point` should be present
