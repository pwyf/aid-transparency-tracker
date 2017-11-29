Feature: Reviews and evaluations

  Scenario Outline: Project performance and evaluation document
    Given the activity is current
     and `activity-status/@code` is one of 3 or 4
     and `default-aid-type/@code` is not G01
     then `document-link/category[@code="A07"]` should be present
