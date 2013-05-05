
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models
import unicodecsv

def downloadUserData():
    fh = urllib2.urlopen(ORG_FREQUENCY_API_URL)
    return _updateOrganisationFrequency(fh)

def importUserDataFromFile():
    filename = 'tests/users.csv'
    with file(filename) as fh:
        return _importUserData(fh)

def _importUserData(fh):

    def getCreateUser(row):
        username = row['username']
        password = row['password']
        name = row['name']
        email_address = row['email_address']
        organisation = row['organisation']

        user = addUser({
            'username': username,
            'password': password,
            'name': name,
            'email_address': email_address,
            'organisation': organisation
        })
        return user

    def getCSOPermissions(organisation_id, 
                role, active, primary, user, permissions):
        if active == 'active':
            permissions.append({
                'user_id': user.id,
                'permission_name': 'cso',
                'permission_method': 'role',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'organisation',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_pwyfreview',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_donorcomments',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_pwyffinal',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_finalised',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            if primary == 'primary':
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'survey_cso',
                    'permission_method': 'edit',
                    'permission_value': organisation_id
                })
        return permissions

    def getDonorPermissions(organisation_id, 
                role, active, primary, user, permissions):
        if active == 'active':
            permissions.append({
                'user_id': user.id,
                'permission_name': 'organisation',
                'permission_method': 'role',
                'permission_value': ''
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'organisation',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_donorreview',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_donorcomments',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            permissions.append({
                'user_id': user.id,
                'permission_name': 'survey_finalised',
                'permission_method': 'view',
                'permission_value': organisation_id
            })
            if primary == 'primary':
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'organisation',
                    'permission_method': 'edit',
                    'permission_value': organisation_id
                })
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'survey_donorreview',
                    'permission_method': 'edit',
                    'permission_value': organisation_id
                })
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'survey_donorcomments',
                    'permission_method': 'edit',
                    'permission_value': organisation_id
                })
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'survey_finalised',
                    'permission_method': 'edit',
                    'permission_value': organisation_id
                })
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'organisations_feedback',
                    'permission_method': 'create',
                    'permission_value': organisation_id
                })
        return permissions

    def generate_permissions():
        permissions = []
        data = unicodecsv.DictReader(fh)
        for row in data:

            user=getCreateUser(row)
            
            organisation_id = row['organisation_id']
            role = row['role']
            active = row['active']
            primary = row['primary']

            if role == 'donor':
                permissions = getDonorPermissions(organisation_id, 
                        role, active, primary, user, permissions)
            elif role == 'CSO':
                permissions = getCSOPermissions(organisation_id, 
                        role, active, primary, user, permissions)
            elif role == 'admin':
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'admin',
                    'permission_method': 'role',
                    'permission_value': ''
                })
            elif role == 'super':
                permissions.append({
                    'user_id': user.id,
                    'permission_name': 'super',
                    'permission_method': 'view',
                    'permission_value': ''
                })
            
        for permission in permissions:
            addUserPermission(permission)

    generate_permissions()

def user(user_id=None):
    if user_id:
        user = models.User.query.filter_by(id=user_id
                    ).first()
        return user
    else:
        users = models.User.query.all()
        return users

def user_by_username(username=None):
    if username:
        user = models.User.query.filter_by(username=username
                    ).first()
        return user
    return None

def addUser(data):
    checkU = models.User.query.filter_by(username=data["username"]
                ).first()
    if not checkU:
        newU = models.User()
        newU.setup(
            username = data["username"],
            password = data["password"],
            name = data.get('name'),
            email_address = data.get('email_address'),
            organisation = data.get('organisation')
        )
        db.session.add(newU)
        db.session.commit()
        return newU
    return checkU

def addUserPermission(data):
    checkP = models.UserPermission.query.filter_by(user_id=data["user_id"],
                permission_name=data["permission_name"],
                permission_method=data.get("permission_method"),
                permission_value=data.get("permission_value")
                ).first()
    if not checkP:
        newP = models.UserPermission()
        newP.setup(
            user_id = data["user_id"],
            permission_name=data["permission_name"],
            permission_method=data.get("permission_method"),
            permission_value=data.get("permission_value")
        )
        db.session.add(newP)
        db.session.commit()
        return newP
    return None

def deleteUserPermission(permission_id):
    checkP = models.UserPermission.query.filter_by(id=permission_id).first()
    if checkP:
        db.session.delete(checkP)
        db.session.commit()
        return True
    return None

def userPermissions(user_id):
    checkP = models.UserPermission.query.filter_by(user_id=user_id
            ).all()
    return checkP
