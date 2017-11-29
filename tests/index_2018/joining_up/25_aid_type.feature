Feature: Aid type

  Scenario Outline: Aid type is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either `default-aid-type` or `transaction/aid-type` should be present

  Scenario Outline: Aid type is valid
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either every `default-aid-type/@code` or `transaction/aid-type/@code` should be on the AidType codelist
