Feature: Objectives

  Scenario Outline: Objectives of activity document
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not G01
     then either `document-link/category[@code="A02"]` or `description[@type="2"]` should be present
