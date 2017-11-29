Feature: Capital spend

  Scenario Outline: Capital spend is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not one of A01, A02 or G01
     and `transaction/aid-type/@code` is not one of A01 or A02
     then `capital-spend` should be present
