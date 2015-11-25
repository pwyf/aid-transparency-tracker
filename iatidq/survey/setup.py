
from iatidq.survey.data import *

def setupSurvey():
    the_publishedstatuses = [
     {'name': 'always',
      'title': 'Always',
      'publishedstatus_class': 'success',
      'publishedstatus_value': 1 },
     {'name': 'sometimes',
      'title': 'Sometimes',
      'publishedstatus_class': 'warning',
      'publishedstatus_value': 0},
     {'name': 'not published',
      'title': 'Not published',
      'publishedstatus_class': 'important',
      'publishedstatus_value': 0}]

    for the_publishedstatus in the_publishedstatuses:
        addPublishedStatus(the_publishedstatus)

    the_publishedformat = [{
      'name': 'machine-readable',
      'title': 'Machine-readable (CSV, Excel)',
      'format_class': 'success',
      'format_value': 1.0 },
     {'name': 'website',
      'title': 'Website',
      'format_class': 'warning',
      'format_value': 0.6666},
     {'name': 'pdf',
      'title': 'PDF',
      'format_class': 'important',
      'format_value': 0.3333},
     {'name': 'document',
      'title': 'Document',
      'format_class': 'success',
      'format_value': 1.0},
     {'name': 'iati',
      'title': 'IATI',
      'format_class': 'success',
      'format_value': 1.0},
     {'name': 'not-applicable',
      'title': 'Format not applicable to this indicator',
      'format_class': 'inverse',
      'format_value': 1.0},
     {'name': 'not-published',
      'title': 'Not published',
      'format_class': 'inverse',
      'format_value': 1.0}]

    for the_publishedformat in the_publishedformat:
        addPublishedFormat(the_publishedformat)

    # workflowtypes define what sort of template is
    # displayed to the user at that workflow stage

    the_workflowTypes = [
    {'name': 'collect',
     'title': 'Initial data collection'},
    {'name': 'send',
     'title': 'Send to next step'},
    {'name': 'review',
     'title': 'Review initial assessment'},
    {'name': 'finalreview',
     'title': "Review donor's review"},
    {'name': 'comment',
     'title': 'Agree/disagree and provide comments on current assessment'},
    {'name': 'agreereview',
     'title': 'Review all comments and reviews and make final decision'},
    {'name': 'finalised',
     'title': 'Survey finalised'}
    ]
    for the_workflowType in the_workflowTypes:    
        addWorkflowType(the_workflowType)
    
    # Workflows are created here.
    # The order attribute defines the ordering
    # of the survey steps.

    def the_workflows():
        return [
            {'name': 'researcher',
             'title': 'Researcher',
             'workflow_type': workflowTypeByName('collect').id,
             'order': 1,
             'duration': 14},
            {'name': 'send',
             'title': 'Send to donor',
             'workflow_type': workflowTypeByName('send').id,
             'order': 2,
             'duration': 2},
            {'name': 'donorreview',
             'title': 'Donor review',
             'workflow_type': workflowTypeByName('review').id,
             'order': 3,
             'duration': 21},
            {'name': 'cso',
             'title': 'Independent review',
             'workflow_type': workflowTypeByName('comment').id,
             'order': 5,
             'duration': None},
            {'name': 'pwyfreview',
             'title': 'PWYF review',
             'workflow_type': workflowTypeByName('review').id,
             'order': 4,
             'duration': 14},
            {'name': 'donorcomments',
             'title': 'Donor comments',
             'workflow_type': workflowTypeByName('comment').id,
             'order': 7,
             'duration': 7},
            {'name': 'pwyffinal',
             'title': 'PWYF final review',
             'workflow_type': workflowTypeByName('finalreview').id,
             'order': 6,
             'duration': 14},
            {'name': 'finalised',
             'title': 'Survey finalised',
             'workflow_type': workflowTypeByName('finalised').id,
             'order': 8,
             'duration': None}
            ]
    for the_workflow in the_workflows():
        addWorkflow(the_workflow)
