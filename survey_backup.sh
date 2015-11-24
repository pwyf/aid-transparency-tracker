#!/bin/bash

DATE=$(date +"%Y%m%d")
pg_dump tracker \
        -t organisation \
        -t workflowtype \
        -t workflow \
        -t indicator \
        -t publishedformat \
        -t publishedstatus \
        -t organisationsurvey \
        -t organisationsurveydata \
> ~/backups/survey_backup_$DATE.sql
