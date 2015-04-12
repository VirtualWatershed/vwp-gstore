from pyramid.response import Response
from pyramid.view import view_config
from pyramid.view import forbidden_view_config
from pyramid.config import Configurator
from pyramid.security import Allow, Authenticated, remember, forget, authenticated_userid, unauthenticated_userid
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from paste.httpheaders import AUTHORIZATION
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPServerError, HTTPBadRequest, HTTPUnprocessableEntity, HTTPUnauthorized
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
#********************************************************************************************************************

@view_config(route_name='changemypassword', renderer='../templates/changemypassword.pt', permission='loggedin')
def changemypassword(request):
    userid = authenticated_userid(request)
    login_url = request.route_url('changemypassword')
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    password = ''
    newpassword1 = ''
    newpassword2 = ''
    if 'form.submitted' in request.params:
        providedpassword = request.params['password']
        newpassword1 = request.params['newpassword1']
        newpassword2 = request.params['newpassword2']
        if newpassword1==newpassword2:
            currentuser = DBSession.query(Users.salt,Users.password).filter(Users.userid==userid).first()
            salt=currentuser.salt
            currentpassword=currentuser.password
            hashed_password = hashlib.sha512(providedpassword + salt).hexdigest()
            new_hashed_password = hashlib.sha512(newpassword1 + salt).hexdigest()
            #if the password matches, then we will change your password to newpassword1
            if hashed_password==currentpassword:
                updatecurrentuser = DBSession.query(Users.password).filter(Users.userid==userid).update({'password': new_hashed_password})
                DBSession.commit()
                print "user %s changed password" % userid
                
                headers = forget(request)
                return HTTPFound(location = came_from, headers = headers)
                message = 'Password has changed, and you have been logged out. Please login with your new password.'
            else:
                    message = 'That is not your current password'
        else:
            message = 'Failed to reset password: you need to type your new password twice.'

    return dict(
        message = message,
        url = request.application_url + '/changemypassword',
        came_from = came_from,
        password = password,
        newpassword1 = newpassword1,
        newpassword2 = newpassword2,
        )




#*********************************************************************************************************************

@view_config(route_name='apicreateuser', permission='createuser')
def apicreateuser(request):
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

@view_config(route_name='createuser', renderer='../templates/createuser.pt', permission='createuser')
def createuser(request):

        login_url = request.route_url('createuser')
        referrer = request.url
        if referrer == login_url:
            referrer = '/'
        came_from = request.params.get('came_from', referrer)
        firstname = ''
        lastname = ''
        email = ''
        address1 = ''
        address2 = ''
        city = ''
        state = ''
        zipcode = ''
        tel_voice = ''
        tel_fax = ''
        country = ''
        message = ''
        userid = ''
        password = ''
        if 'form.submitted' in request.params:
            userid = request.params['userid']
            password = request.params['password']
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

            logmessage="User created: %s" % userid
            print logmessage
            existUser=DBSession.query(Users.userid).filter(Users.userid==userid).first()
            print "Existing user?: %s" % existUser

            if(existUser):
                print "Can't add %s, User already exists" % userid
                message="Can't add user, userid exists in database"
            else:
                newuser = Users(userid=userid,firstname=firstname,lastname=lastname,city=city,address1=address1,address2=address2,state=state,zipcode=zipcode,tel_voice=tel_voice,tel_fax=tel_fax,country=country,email=email,salt=salt,password=hashed_password)
                try:
                    DBSession.add(newuser)
                    DBSession.commit()
                    DBSession.flush()
                    DBSession.refresh(newuser)
                    message="User created: %s" % userid

                except Exception as err:
                    return HTTPServerError(err)


        return dict(
            url = request.application_url + '/createuser',
            came_from = came_from,
            firstname = firstname,
            lastname = lastname,
            email = email,
            address1 = address1,
            address2 = address2,
            city = city,
            state = state,
            zipcode = zipcode,
            tel_voice = tel_voice,
            tel_fax = tel_fax,
            country = country,
            message = message,
            userid = userid,
            password = password,
            )


#****************************************************************************************************************
@view_config(route_name='login', renderer='../templates/login.pt')
@forbidden_view_config(renderer='../templates/login.pt')
def login(request):

        login_url = request.route_url('login')
        referrer = request.url
        if referrer == login_url:
            referrer = '/' # never use the login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        userid = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            formuserid = request.params['login']
            formpassword = request.params['password']

            checkuser = DBSession.query(Users.userid,Users.salt,Users.password).filter(Users.userid==formuserid).first()

            if(checkuser==None):
                message = 'Bad username or password.'

            else:

                username=checkuser.userid
                salt=checkuser.salt
                passwd=checkuser.password

                hashed_password = hashlib.sha512(formpassword + salt).hexdigest()
                #if the passwords match then you get a cookie
                if formuserid == username and hashed_password==passwd:
                    headers = remember(request, formuserid)
                 #   return Response('Logged in as %s' % formuserid, headers=headers)
                    message = 'Logged in as %s' % formuserid
                    return HTTPFound(location = came_from, headers = headers)
                else:
                    message = 'Bad username or password'
                    #return Response('Bad username or password')


        return dict(
            message = message,
            url = request.application_url + '/login',
            came_from = came_from,
            login = login,
            password = password,
            )



#****************************************************************************************************************

@view_config(route_name='apilogin')
def apilogin(request):
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
        if(checkuser==None):
            return HTTPUnauthorized("Bad username or password.")

        else:
            username=checkuser.userid
            salt=checkuser.salt
	    passwd=checkuser.password
            hashed_password = hashlib.sha512(password + salt).hexdigest()

        if userid == username and hashed_password==passwd:

            headers = remember(request, userid)
            return Response('Logged in as %s' % userid, headers=headers)
        else:
            return HTTPUnauthorized('Bad username or password')


    #else if the user is using form based auth with the user and pass as part of the url...
    elif formuserid:

        #query database with userid and return hash and salt
        checkuser = DBSession.query(Users.userid,Users.salt,Users.password).filter(Users.userid==formuserid).first()
        if(checkuser==None):
            return HTTPUnauthorized("Bad username or password.")

        else:
            username=checkuser.userid
            salt=checkuser.salt
            passwd=checkuser.password
            hashed_password = hashlib.sha512(formpassword + salt).hexdigest()
        #if the passwords match then you get a cookie
        if formuserid == username and hashed_password==passwd:
            headers = remember(request, formuserid)
            return Response('Logged in as %s' % formuserid, headers=headers)
        else:
            return HTTPUnauthorized('Bad username or password')
    #if neither are givin...
    else:
        return Response('A username and password is required')

#*********************************************************************************************************************

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return Response('Logged out', headers=headers)

#*********************************************************************************************************************
