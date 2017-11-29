Feature: Organisation strategy

  Scenario: Organisation strategy is present
    Given file is an organisation file
     then `document-link/category[@code="B02"]` should be present
