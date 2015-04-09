from pyramid.response import Response
from pyramid.view import view_config
from pyramid.config import Configurator
from pyramid.security import Allow, Authenticated, remember, forget, authenticated_userid, unauthenticated_userid
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from paste.httpheaders import AUTHORIZATION
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPServerError, HTTPBadRequest, HTTPUnprocessableEntity

from ..models import DBSession
from ..models.users import (
    Users,
    )

import binascii
import base64
import hashlib
import os

#*********************************************************************************************************************

@view_config(route_name='private', permission='test')
def delete(request):
    print authenticated_userid(request)
    return Response('This is for testing auth.')

@view_config(route_name='createuser', permission='createuser')
def createuser(request):
    userid = request.params['userid']
    firstname = request.params['firstname']
    lastname = request.params['lastname']
    email = request.params['email']
    password = request.params['password']
    address1 = request.params['address1'] 
    address2 = request.params['address2']
    city = request.params['city']
    state = request.params['state']
    zipcode = request.params['zipcode']
    tel_voice = request.params['tel_voice']
    tel_fax = request.params['tel_fax']
    country = request.params['country']
    salt = os.urandom(33).encode('base_64')
    hashed_password = hashlib.sha512(password + salt).hexdigest()    

    print "city: %s" % city

    existUser=DBSession.query(Users.userid).filter(Users.userid==userid).first()
    print "Existing user?: %s" % existUser

    if(existUser):
	    print "Can't add %s, User already exists" % userid
            return HTTPUnprocessableEntity("Can't add user, user already exists in database")

    else:
	    newuser = Users(userid=userid,firstname=firstname,lastname=lastname,city=city,address1=address1,address2=address2,state=state,zipcode=zipcode,tel_voice=tel_voice,tel_fax=tel_fax,country=country,email=email,salt=salt,password=hashed_password)
	    try:
	        DBSession.add(newuser)
	        DBSession.commit()
	        DBSession.flush()
	        DBSession.refresh(newuser)
		message="User created: %s" % userid
		return Response(message)

	    except Exception as err:
	        return HTTPServerError(err)



#****************************************************************************************************************

@view_config(route_name='login')
def login(request):
    formuserid = request.params.get('userid') if 'userid' in request.params else ''
    formpassword = request.params.get('password') if 'password' in request.params else ''
    auth = request.environ.get('HTTP_AUTHORIZATION') 
    #if the user is using basic auth...
    if auth:
        try:
            authmeth, auth = auth.split(' ', 1)
        except AttributeError as ValueError:  # not enough values to unpack
            return None

        if authmeth.lower() != 'basic':
            return None

        try:
            # Python 3's string is already unicode
            auth = base64.b64decode(auth.strip())
        except binascii.Error:  # can't decode
            return None

        if not isinstance(auth, unicode):
            auth = auth.decode('utf-8')

        try:
            userid, password = auth.split(':', 1)
        except ValueError:  # not enough values to unpack
            return None

	#query database with userid and return hash and salt
	checkuser = DBSession.query(Users.userid,Users.salt,Users.password).filter(Users.userid==userid).first()
	username=checkuser[0]
        salt=checkuser[1]
	passwd=checkuser[2]
    	
        hashed_password = hashlib.sha512(password + salt).hexdigest()

        if userid == username and hashed_password==passwd:

            headers = remember(request, userid)
            return Response('Logged in as %s' % userid, headers=headers)
        else:
            return Response('Bad username or password')


    #else if the user is using form based auth with the user and pass as part of the url...
    elif formuserid:

        #query database with userid and return hash and salt
        checkuser = DBSession.query(Users.userid,Users.salt,Users.password).filter(Users.userid==formuserid).first()
        username=checkuser[0]
        salt=checkuser[1]
        passwd=checkuser[2]

        hashed_password = hashlib.sha512(formpassword + salt).hexdigest()
        #if the passwords match then you get a cookie
        if formuserid == username and hashed_password==passwd:
            headers = remember(request, formuserid)
            return Response('Logged in as %s' % formuserid, headers=headers)
        else:
            return Response('Bad username or password')
    #if neither are givin...
    else:
        return Response('A username and password is required')

#*********************************************************************************************************************

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return Response('Logged out', headers=headers)

#*********************************************************************************************************************
