Feature: Results

  Scenario Outline: Results data
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not G01
     then `result` should be present

  Scenario Outline: Results document
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not G01
     then `document-link/category[@code="A08"]` should be present
