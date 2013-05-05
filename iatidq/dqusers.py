
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models

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
            email_address = data.get('name')
        )
        db.session.add(newU)
        db.session.commit()
        return newU
    return None

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

def userPermissions(user_id):
    checkP = models.UserPermission.query.filter_by(user_id=user_id
            ).all()
    return checkP
