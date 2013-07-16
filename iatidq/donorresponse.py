
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

RESPONSE_TYPES = {
    '': {
        'id': None,
        'text': "",
        'description': ""
    },
    'reviewed': {
        'id': 0,
        'text': 'reviewed',
        'description': "reviewed this survey"
    },
    'emailresponse': {
        'id': 3,
        'text': 'replied by email',
        'description': "responded by email, and provided general comments, but not specific comments"
    },
    'declined': {
        'id': 5,
        'text': 'declined to review',
        'description': "responded by email, but declined to review the survey"
    },
    'noreply': {
        'id': 6,
        'text': 'did not respond',
        'description': "did not respond to our attempts to contact them"
    }
}

RESPONSE_IDS = dict(map(lambda x: (x[1]["id"], {
                            "id": x[0], 
                            "text": x[1]["text"], 
                            "description": x[1]["description"]
                            }), RESPONSE_TYPES.items()))
