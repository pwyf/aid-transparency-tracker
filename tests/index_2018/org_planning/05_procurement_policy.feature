Feature: Procurement policy

  Scenario: Procurement policy is present
    Given file is an organisation file
     then `document-link/category[@code="B05"]` should be present
