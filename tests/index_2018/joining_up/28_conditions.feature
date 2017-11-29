Feature: Conditions

  Scenario Outline: Conditions data
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then `conditions` should be present

  Scenario Outline: Conditions document
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then `document-link/category[@code="A04"]` should be present
