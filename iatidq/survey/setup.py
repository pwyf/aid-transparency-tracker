
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
    
    # Workflows need to be created and then 
    # updated with the leadsto attribute.
    # They define what happens to the survey
    # at each step.

    def the_workflows():
        return [
            {'name': 'researcher',
             'title': 'Researcher',
             'workflow_type': workflowTypeByName('collect').id,
             'leadsto': getIDorNone(workflowByName('send')),
             'duration': 14},
            {'name': 'send',
             'title': 'Send to donor',
             'workflow_type': workflowTypeByName('send').id,
             'leadsto': getIDorNone(workflowByName('donorreview')),
             'duration': 2},
            {'name': 'donorreview',
             'title': 'Donor review',
             'workflow_type': workflowTypeByName('review').id,
             'leadsto': getIDorNone(workflowByName('pwyfreview')),
             'duration': 21},
            {'name': 'cso',
             'title': 'Independent review',
             'workflow_type': workflowTypeByName('comment').id,
             'leadsto': getIDorNone(workflowByName('pwyffinal')),
             'duration': None},
            {'name': 'pwyfreview',
             'title': 'PWYF review',
             'workflow_type': workflowTypeByName('review').id,
             'leadsto': getIDorNone(workflowByName('cso')),
             'duration': 14},
            {'name': 'donorcomments',
             'title': 'Donor comments',
             'workflow_type': workflowTypeByName('comment').id,
             'leadsto': getIDorNone(workflowByName('finalised')),
             'duration': 7},
            {'name': 'pwyffinal',
             'title': 'PWYF final review',
             'workflow_type': workflowTypeByName('finalreview').id,
             'leadsto': getIDorNone(workflowByName('donorcomments')),
             'duration': 14},
            {'name': 'finalised',
             'title': 'Survey finalised',
             'workflow_type': workflowTypeByName('finalised').id,
             'leadsto': None,
             'duration': None}
            ]
    for the_workflow in the_workflows():
        addWorkflow(the_workflow)

    # This will correct leadsto values
    for the_workflow in the_workflows():
        updateWorkflow(the_workflow)
