Feature: Flow type

  Scenario Outline: Flow type
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either `default-flow-type` or `transaction/flow-type` should be present

  Scenario Outline: Flow type uses standard codelist
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either every `default-flow-type/@code` or `transaction/flow-type/@code` should be on the FlowType codelist
