test_to_kind = {
    "Organisation strategy": "org-document",
    "Annual report": "org-document",
    "Allocation policy": "org-document",
    "Procurement policy": "org-document",
    "Audit": "org-document",
    "Location (sub-national)": "location",
    "Location (sub-national) coordinates or point": "location",
    "Project budget document": "document",
    "Project budget document": "document",
    "Conditions document": "document",
    "Contract document": "document",
    "Tenders document": "document",
    "Objectives of activity document": "document",
    "Pre- and post-project impact appraisal documents": "document",
    "Project performance and evaluation document": "document",
    "Results document": "document",
    "Results data": "result",
    "Conditions data": "conditions",
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
