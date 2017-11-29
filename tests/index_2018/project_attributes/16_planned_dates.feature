Feature: Planned dates

  Scenario Outline: Planned start date is present
    Given the activity is current
     then `activity-date[@type="1"] | activity-date[@type="start-planned"]` should be present

  Scenario Outline: Planned end date is present
    Given the activity is current
     then `activity-date[@type="3"] | activity-date[@type="end-planned"]` should be present
