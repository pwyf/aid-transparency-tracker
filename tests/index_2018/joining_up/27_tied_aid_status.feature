Feature: Tied aid status

  Scenario Outline: Tied aid status
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either `default-tied-status` or `transaction/tied-status` should be present

  Scenario Outline: Tied aid status uses standard codelist
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either every `default-tied-status/@code` or `transaction/tied-status/@code` should be on the TiedStatus codelist
