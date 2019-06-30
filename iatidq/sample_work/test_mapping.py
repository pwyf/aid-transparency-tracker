test_to_kind = {
    "Project budget document": "document",
    "Contract document": "document",
    "Tenders document": "document",
    "Conditions data": "conditions",
    "Conditions document": "document",
    "Objectives of activity document": "document",
    "Pre-project impact appraisal documents": "document",
    "Project performance and evaluation document": "document",
    "Results document": "document",
    "Results data": "result",
    "Title": "text",
    "Description": "text",
    "Location (sub-national)": "location",
    "Location (sub-national) coordinates or point": "location",
}

## Integers 2, 3, 4, etc. Are the response integer that goes into
## sample_work_item table.

kind_to_status = {
    "text": {
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
              "text:": "specific to the activity",
              "button": "not specific to activity",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3:
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy definition",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
    },
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
              "button": "not specific to activity",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
        4:
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy definition",
              "icon": "remove",
              "class": "danger",
              "value": "4",
            },
        5:
            {
              "text:": "current",
              "button": "document out of date",
              "icon": "remove",
              "class": "danger",
              "value": "5",
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
              "button": "no results information",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3:
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy definition",
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
              "button": "no conditions information",
              "icon": "remove",
              "class": "danger",
              "value": "2",
            },
        3:
            {
              "text:": "satisfies the definition",
              "button": "doesn't satisfy definition",
              "icon": "remove",
              "class": "danger",
              "value": "3",
            },
        4:
            {
              "text:": "document is current",
              "button": "document out of date",
              "icon": "remove",
              "class": "danger",
              "value": "4",
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
              "button": "no contain location information",
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
