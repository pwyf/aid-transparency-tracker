Feature: Finance type

  Scenario Outline: Default finance type
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either `default-finance-type` or `transaction/finance-type` should be present

  Scenario Outline: Finance type uses standard codelist
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     then either every `default-finance-type/@code` or `transaction/finance-type/@code` should be on the FinanceType codelist
