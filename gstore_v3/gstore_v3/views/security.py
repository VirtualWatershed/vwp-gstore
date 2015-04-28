import sqlalchemy
from sqlalchemy import desc, asc, func
from sqlalchemy.sql.expression import and_, or_, cast
from sqlalchemy.sql import between

from ..models import DBSession
from ..models.groups import Groups
from ..models.users import Users

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
