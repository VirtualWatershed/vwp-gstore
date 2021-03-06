from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from pyramid.threadlocal import get_current_registry

from .models import DBSession
from .models.datasets import *

#TODO: set up a better default - like the api docs currently
@view_config(route_name='home', renderer='templates/home.pt')
def my_view(request):
    try:
        #get the host url
        host = request.host_url
        g_app = request.script_name[1:]

        base_url = get_current_registry().settings['BALANCER_URL']
        
        one = DBSession.query(Dataset).filter(Dataset.id==143533).first()
        one = ''
    except DBAPIError as e:
        return Response(str(e), content_type='text/plain', status_int=500)
    return dict(logged_in = request.authenticated_userid, base_url = base_url)

conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_gstore_v3_db" script
    to initialize your database tables.  Check your virtual 
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

