Feature: Unique ID

  Scenario Outline: IATI Identifier is present
    Given the activity is current
     then `iati-identifier` should be present

  Scenario Outline: IATI Identifier starts with reporting org ref
    Given the activity is current
     then `iati-identifier/text()` should start with either `reporting-org/@ref` or `other-identifier[@type="B1"]/@ref`
