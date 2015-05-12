from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPServerError, HTTPBadRequest, HTTPUnprocessableEntity

import sqlalchemy
from sqlalchemy import desc, asc, func
from sqlalchemy.sql.expression import and_, or_, cast
from sqlalchemy.sql import between

from ..models import DBSession
from ..models.groups import Groups
from ..models.users import Users

@view_config(route_name='group_manager_frontend', renderer='../templates/groupmanager.pt', permission='admin')
def groupmanagerfrontend(request):
    print "look at my frontend"
    userid = request.params.get('userid') if 'userid' in request.params else ''
    groupname = request.params.get('groupname') if 'groupname' in request.params else ''
    message = ''
    if 'form.added' in request.params:
        userid = request.params['userid']
        groupname = request.params['groupname']

        user = DBSession.query(Users).filter(Users.userid==userid).first()
        group = DBSession.query(Groups).filter(Groups.groupname==groupname).first()
        if user and group:
            print "Adding " + userid + " to " + groupname
            if group not in user.groups:
                user.groups.append(group)
                DBSession.commit()
                message="Successfully added " + userid + " to " + groupname
            else:
                message=userid + " is already in " + group
        else:
            message="Unknown user or group name"

    if 'form.removed' in request.params:
        userid = request.params['userid']
        groupname = request.params['groupname']
        print userid + " + " + groupname

        user = DBSession.query(Users).filter(Users.userid==userid).first()
        group = DBSession.query(Groups).filter(Groups.groupname==groupname).first()
        if user and group:
            print "Removing " + userid + " to " + groupname
            if group in user.groups:
                user.groups.remove(group)
                DBSession.commit()
                message="Successfully removed " + userid + " from " + groupname
            else:
                message=userid + " is not in " + group
        else:
            message="Unknown user or group name"

    return dict(
        message = message,
        url = request.application_url + '/admin/groupmanager',
        userid = userid,
        groupname = groupname
    )
    

@view_config(route_name='group_manager', permission='admin')
def groupmanager(request):
    userid = request.params.get('userid') if 'userid' in request.params else ''
    groupname = request.params.get('groupname') if 'groupname' in request.params else ''
    managemode = request.params.get('managemode') if 'managemode' in request.params else ''

    if userid and groupname and managemode:
        user = DBSession.query(Users).filter(Users.userid==userid).first()
        group = DBSession.query(Groups).filter(Groups.groupname==groupname).first()
        if user and group:
            if managemode == '1':
                print "Adding " + userid + " to " + groupname
                if group not in user.groups:
                    user.groups.append(group)
                    DBSession.commit()
                else:
                    return HTTPBadRequest(userid + " is already in " + groupname)
            elif managemode == '0':
                print "Removing " + userid + " from " + groupname
                if group in user.groups:
                    user.groups.remove(group)
                    DBSession.commit()
                else:
                    return HTTPBadRequest(userid + " is not in " + groupname)
            else:
                return HTTPBadRequest("Improper management mode: %s" %managemode)
        else:
            return HTTPBadRequest("Unknown user or group name")
    else:
        return HTTPBadRequest("Must provide user id, group name and proper management mode")

    return Response('200')

def groupfinder(userid, request):
    #groups = DBSession.query(Groups.groupname).join(Users.groups).filter(and_(Users.userid=='hays.barrett')).all()
    #response = Response(json.dumps(groups))
    #response.content_type = 'application/json'
    #return response
    
    groups = DBSession.query(Groups.groupname).join(Users.groups).filter(Users.userid==userid).all()
    print groups
    grouplist = []
    for group in groups:
        grouplist.append('group:'+group[0].decode('utf-8'))
    #if userid in USERS:
    #    return GROUPS.get(userid, [])
    print grouplist
    return grouplist
