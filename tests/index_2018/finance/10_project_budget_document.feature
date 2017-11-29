Feature: Budget document

  Scenario Outline: Budget document is present
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not one of A01, A02 or G01
     and `transaction/aid-type/@code` is not one of A01 or A02
     then `document-link/category[@code="A05"]` should be present
