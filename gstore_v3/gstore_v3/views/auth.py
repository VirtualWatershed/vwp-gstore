
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
            html = """\
            <html>
             <head></head>
              <body>
              <img width="443" height="98" alt="VWP" src="data:image/png;base64,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">
               <p>Someone has requested a link to change your password.<br>
                You can reset your password by clicking the link below:<br>
                %s
               </p>
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
            pwtest=passcheck(password)
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
                                        A new account has been created for you on vwp-dev.unm.edu<br />
                                        You can set your password by clicking the link below<span style="font-weight: bold;">:<br />
                                          <br />
                                          <h4>%s</h4>
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
