test_to_kind = {
    "document-link/category[@code='B02'] exists?": "org-document",
	"document-link/category[@code='B01'] exists?": "org-document",
	"document-link/category[@code='B04'] exists?": "org-document",
    "document-link/category[@code='B05'] exists?": "org-document",
	"document-link/category[@code='B06'] exists?": "org-document",
    "location exists (if activity-status/@code is at least 2 and recipient-region/@code is not 998)?": "location",
    "location/coordinates exists (if activity-status/@code is at least 2 and recipient-region/@code is not 998)?": "location",
    "location/coordinates or location/point exists (if activity-status/@code is at least 2 and recipient-region/@code is not 998)?": "location",
    "document-link/category[@code='A09'] exists (if activity-status/@code is at least 2)?": "document",
    "document-link/category[@code='A07'] exists (if activity-status/@code is at least 3)?": "document",
    "document-link/category[@code='A02'] or description[@type='2'] exists (if activity-status/@code is at least 2)?": "document",
	"document-link/category[@code='A05'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
	"document-link/category[@code='A06'] or document-link/category[@code='A11'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
    "document-link/category[@code='A10'] exists (if activity-status/@code is at least 2 and (default-aid-type/@code or transaction/aid-type/@code is not A01))?": "document",
    "document-link/category[@code='A08'] exists (if activity-status/@code is at least 2)?": "document",
    "result exists (if activity-status/@code is at least 2)?": "result",
    "document-link/category[@code='A01'] exists (if activity-status/@code is at least 2)?": "document",
    "document-link/category[@code='A04'] exists (if activity-status/@code is at least 2)?": "document",
    "conditions exists (if activity-status/@code is at least 2)?": "conditions",
}

## Integers 2, 3, 4, etc. Are the response integer that goes into
## sample_work_item table.

kind_to_status = {
    "document": {
        1:
            {
              "text:": "pass",
              "button": "pass",
              "icon": "ok",
              "class": "success",
              "value": "1",
            },
        2:
            {
              "text:": "able to access",
              "button": "unable to access",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3: 
            {
              "text:": "specific to the activity",
              "button": "not specific to the activity",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
        4: 
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy the definition",
              "icon": "remove",
              "class": "danger",
              "value": "4",
            },
    },
    "result": {
        1:
            {
              "text:": "pass",
              "button": "pass",
              "icon": "ok",
              "class": "success",
              "value": "1",
            },
        2:
            {
              "text:": "contains results information",
              "button": "doesn't contain results information",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3: 
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy the definition",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
    },
    "conditions": {
        1:
            {
              "text:": "pass",
              "button": "pass",
              "icon": "ok",
              "class": "success",
              "value": "1",
            },
        2:
            {
              "text:": "contains conditions information",
              "button": "doesn't contain conditions information",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3: 
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy the definition",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
    },
    "location": {
        1:
            {
              "text:": "pass",
              "button": "pass",
              "icon": "ok",
              "class": "success",
              "value": "1",
            },
        2:
            {
              "text:": "contains location information",
              "button": "doesn't contain location information",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3: 
            {
              "text:": "consistent with documentation",
              "button": "not consistent with documentation",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
    },
}
    
"""
org-document 	able to access 	unable to access
org-document 	satisfies the definition 	doesn't satisfy the definition
org-document 	document is current 	document isn't current
"""
