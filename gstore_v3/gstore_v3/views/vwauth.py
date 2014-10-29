from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPServerError, HTTPBadRequest

from sqlalchemy import desc, asc, func
from sqlalchemy.sql.expression import and_, cast
from sqlalchemy.sql import between
import sqlalchemy

import os, json, re
from xml.sax.saxutils import escape

from ..models import DBSession
from ..models.model_runs import (
    Modelruns,
    )
from ..models.datasets import Dataset, Category

from ..lib.mongo import gMongo, gMongoUri
from ..lib.utils import *
from ..lib.spatial import *
from ..lib.database import get_dataset


'''
{"description": "Your text here"}
'''


@view_config(route_name='check_auth', request_method='GET')
def check_auth(auth):
    return Response('True')    

