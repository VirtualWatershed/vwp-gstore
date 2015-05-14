
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
from ..models.password_reset_codes import (
    Password_Reset_Codes,
    )


import binascii
import base64
import hashlib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

#*********************************************************************************************************************
def passcheck(passwd):
    if len(passwd) >=8:
        if set('[~!@#$%^&*()_+{}":;\']+$').intersection(passwd):
            if set('abcdefghijklmnopqrstuvwxyz').intersection(passwd):
                if set('ABCDEFGHIJKLMNOPQRSTUVWXYZ').intersection(passwd):
                    if set('0123456789').intersection(passwd):
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False
#*********************************************************************************************************************

@view_config(route_name='private', permission='test')
def delete(request):
    print authenticated_userid(request)

    return Response('This is for testing auth.')
#********************************************************************************************************************

@view_config(route_name='passwordreset', renderer='../templates/passwordreset.pt')
def passwordreset(request):
    email = ''
    message = ''

    if 'form.submitted' in request.params:
        email = request.params['email']
        checkemail = DBSession.query(Users.userid,Users.salt).filter(Users.email==email).first()
        if(checkemail==None):
            message = 'email address not found'
        else:        
            userid=checkemail.userid
            randomcode = uuid.uuid4().hex
            salt=checkemail.salt
            resetcode = hashlib.sha512(randomcode + salt).hexdigest()
            #for use in e-mail
            base_url = request.registry.settings['BALANCER_URL_SECURE']
            resetpath = "/reset?resetcode="
            reseturl = base_url + resetpath + resetcode
            checkuserid = DBSession.query(Password_Reset_Codes.userid).filter(Password_Reset_Codes.userid==userid).first()                    
            #for multiple attempts at reset password requests.
            if(checkuserid!=None):
                d=DBSession.query(Password_Reset_Codes.resetcode).filter(Password_Reset_Codes.userid==userid).delete()
                DBSession.commit()
            newcode = Password_Reset_Codes(userid=userid, resetcode=resetcode)            
            DBSession.add(newcode)
            DBSession.commit()
            DBSession.flush()
            DBSession.refresh(newcode)
            message = 'email has been sent to %s' % email
            me = "wcwave@edac.unm.edu"
            you = email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "VWP password reset"
            msg['From'] = me
            msg['To'] = you
            text = "Someone has requested a link to change your password.\nYou can reset by using the link below:\n%s" % reseturl
            html = """<!DOCTYPE html>
                      <html xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
                        <head>
                          <meta charset="UTF-8" />
                          <title>Password Reset</title>
                        </head>
                        <body>
                          <div id="wrap">
                            <div id="top-small">
                              <div class="top-small align-center">
                                <div style="text-align: center;" id="bg"> <img height="98" width="443"
                                    src="http://vwp-dev.unm.edu/static/WC-WAVE_final2_0.png" alt="VWP" />
                                </div>
                              </div>
                            </div>
                            <div id="middle" style="background:#E6E6E6">
                              <div class="middle align-right">
                                <div class="app-welcome align-left" id="left"> <b>Password Reset</b><br />
                                </div>
                              </div>
                            </div>
                            <div id="bottom">
                              <div class="bottom"> <br />
                                A request to reset your VWP password has been made.<br />
                                You can reset your password by clicking the link below: <span style="font-weight: bold;">:<br />
                                  <br />
                                  <h4><a href="%s">Change Password</a></h4>
                                </span> <br />
                              </div>
                            </div>
                          </div>
                          <div id="footer">
                            <div class="footer"><br />
                            </div>
                          </div>
                        </body>
                      </html>
            """ % reseturl

            # Record the MIME types of both parts - text/plain and text/html.
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')

            # Attach parts into message container.
            msg.attach(part1)
            msg.attach(part2)

            # Send the message via local SMTP server.
            s = smtplib.SMTP('edacmail.unm.edu')
            # sendmail function takes 3 arguments: sender's address, recipient's address
            s.sendmail(me, you, msg.as_string())
            s.quit()


    return dict(
        message = message,
        url = request.application_url + '/passwordreset',
        email = email,
        )


#********************************************************************************************************************

@view_config(route_name='reset', renderer='../templates/reset.pt')
def reset(request):
    resetcode=request.params['resetcode']
    #login_url = request.route_url('login')
    #referrer = request.url
    #if referrer == login_url:
    #    referrer = '/' # never use the login form itself as came_from
    referrer = '/'
    came_from = request.params.get('came_from', referrer)

    message = ''
    password = ''
    password2 = ''
    if 'form.submitted' in request.params:
        password = request.params['password']
        password2 = request.params['password2']
        if password==password2:
            pwtest=passcheck(password)
            if pwtest is True:
                checkresetcode = DBSession.query(Password_Reset_Codes.userid).filter(Password_Reset_Codes.resetcode==resetcode).first()
                if(checkresetcode==None):
                    message = 'Bad resetcode. Are you using the link provided?'

                else:
                    userid=checkresetcode.userid
                    getsalt = DBSession.query(Users.salt).filter(Users.userid==userid).first()
                    salt=getsalt.salt
                    new_hashed_password = hashlib.sha512(password + salt).hexdigest()
                    updatecurrentuser = DBSession.query(Users.password).filter(Users.userid==userid).update({'password': new_hashed_password})
                    DBSession.commit()
                    print "user %s changed password" % userid
                    headers = forget(request)
                    d=DBSession.query(Password_Reset_Codes.resetcode).filter(Password_Reset_Codes.userid==userid).delete()
                    DBSession.commit()
                    message = 'Your password has changed.'
                    return HTTPFound(location = came_from, headers = headers)
            else:
                message = 'Your passsword must be at least 8 characters long and have upper case, lowercase, number, and a specal character.'



        else:
            message = 'The two password fields must match'


    return dict(
        message = message,
        url = request.application_url + '/reset',
        came_from = came_from,
        password = password,
        password2 = password2,
        resetcode = resetcode,
        )


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
            pwtest=passcheck(newpassword1)
            if pwtest is True:
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
                message = 'Your passsword must be at least 8 characters long and have upper case, lowercase, number, and a specal character.'
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

#        login_url = request.route_url('createuser')
 #       referrer = request.url
  #      if referrer == login_url:
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
 #       password = ''
        if 'form.submitted' in request.params:
            userid = request.params['userid']
            firstname = request.params['firstname']
            lastname = request.params['lastname']
            email = request.params['email']
#            password = request.params['password']
            address1 = request.params['address1']
            address2 = request.params['address2']
            city = request.params['city']
            state = request.params['state']
            zipcode = request.params['zipcode']
            tel_voice = request.params['tel_voice']
            tel_fax = request.params['tel_fax']
            country = request.params['country']
            salt = os.urandom(33).encode('base_64')
            password = os.urandom(33).encode('base_64')
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
                    randomcode = uuid.uuid4().hex
                    resetcode = hashlib.sha512(randomcode + salt).hexdigest()
                    base_url = request.registry.settings['BALANCER_URL_SECURE']
                    resetpath = "/reset?resetcode="
                    reseturl = base_url + resetpath + resetcode
                    newcode = Password_Reset_Codes(userid=userid, resetcode=resetcode)
                    DBSession.add(newcode)
                    DBSession.commit()
                    DBSession.flush()
                    DBSession.refresh(newcode)
                    me = "wcwave@edac.unm.edu"
                    you = email
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = "Your VWP Account"
                    msg['From'] = me
                    msg['To'] = you
                    text = "Set your password by using the link below:\n%s" % reseturl
                    html = """<!DOCTYPE html>
                              <html xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
                                <head>
                                  <meta charset="UTF-8" />
                                  <title>New VWP Account</title>
                                </head>
                                <body>
                                  <div id="wrap">
                                    <div id="top-small">
                                      <div class="top-small align-center">
                                        <div style="text-align: center;" id="bg"> <img height="98" width="443"
                                            src="http://vwp-dev.unm.edu/static/WC-WAVE_final2_0.png" alt="VWP" />
                                        </div>
                                      </div>
                                    </div>
                                    <div id="middle" style="background:#E6E6E6">
                                      <div class="middle align-right">
                                        <div class="app-welcome align-left" id="left"> <b>New Account</b><br />
                                        </div>
                                      </div>
                                    </div>
                                    <div id="bottom">
                                      <div class="bottom"> <br />
                                        A new account has been created for you on vwp-dev.unm.edu with username:<strong> %s </strong><br />
                                        You can set your password by clicking the link below<span style="font-weight: bold;">:<br />
                                          <br />
                                          <h4><a href='%s'>Create Password</a></h4>
                                        </span> <br />
                                      </div>
                                    </div>
                                  </div>
                                  <div id="footer">
                                    <div class="footer"><br />
                                    </div>
                                  </div>
                                </body>
                              </html>
                          """ % (userid,reseturl)

                    # Record the MIME types of both parts - text/plain and text/html.
                    part1 = MIMEText(text, 'plain')
                    part2 = MIMEText(html, 'html')

                    # Attach parts into message container.
                    msg.attach(part1)
                    msg.attach(part2)

                    # Send the message via local SMTP server.
                    s = smtplib.SMTP('edacmail.unm.edu')
                    s.set_debuglevel(1)
                    # sendmail function takes 3 arguments: sender's address, recipient's address
                    s.sendmail(me, you, msg.as_string())
                    s.quit()
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
