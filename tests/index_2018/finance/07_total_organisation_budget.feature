Feature: Total organisation budget

  Scenario: Organisation budget available one year forward
    Given file is an organisation file
     then `total-budget` should be available 1 year forward

  Scenario: Organisation budget available two years forward
    Given file is an organisation file
     then `total-budget` should be available 2 years forward

  Scenario: Organisation budget available three years forward
    Given file is an organisation file
     then `total-budget` should be available 3 years forward
