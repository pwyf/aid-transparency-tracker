Feature: Current status

  Scenario Outline: Current status is present
    Given the activity is current
     then `activity-status` should be present

  Scenario Outline: Current status is valid
    Given the activity is current
     then every `activity-status/@code` should be on the ActivityStatus codelist
