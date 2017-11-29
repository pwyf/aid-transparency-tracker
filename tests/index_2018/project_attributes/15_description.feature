Feature: Description

  Scenario Outline: Description is present
    Given the activity is current
     then either `description/text()` or `description/narrative/text()` should be present

  Scenario Outline: Description has at least 80 characters
    Given the activity is current
     then either `description/text()` or `description/narrative/text()` should have at least 80 characters
