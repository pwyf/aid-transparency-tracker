Feature: Allocation policy

  Scenario: Allocation policy is present
    Given file is an organisation file
     then `document-link/category[@code="B04"]` should be present
