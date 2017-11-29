Feature: Budget

  Scenario Outline: Budget available forward annually
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not G01
     and either `activity-date[@type="3"]/@iso-date` or `activity-date[@type="4"]/@iso-date` is at least 6 months ahead
     then either `budget` or `planned-disbursement` should be available forward annually

  Scenario Outline: Budget available forward quarterly
    Given the activity is current
     and `activity-status/@code` is one of 2, 3 or 4
     and `default-aid-type/@code` is not G01
     and either `activity-date[@type="3"]/@iso-date` or `activity-date[@type="4"]/@iso-date` is at least 6 months ahead
     then either `budget` or `planned-disbursement` should be available forward quarterly
