Feature: Sector

  Scenario Outline: Sector is present
    Given the activity is current
     then either `sector` or `transaction/sector` should be present

  Scenario Outline: Sector uses DAC CRS 5 digit purpose codes
    Given the activity is current
     then every `sector[@vocabulary="DAC"]/@code | sector[not(@vocabulary)]/@code | sector[@vocabulary="1"]/@code | transaction/sector[@vocabulary="1"]/@code | transaction/sector[not(@vocabulary)]/@code` should be on the Sector codelist
