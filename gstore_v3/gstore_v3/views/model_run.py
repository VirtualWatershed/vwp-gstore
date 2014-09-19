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

@view_config(route_name='add_model_id', request_method='POST')
def add_model_id(request):
    provided_uuid = generate_uuid4()
    dataset_uuid = str(provided_uuid)
    app = request.matchdict['app']
    description=request.json['description']
    modelrun = Modelruns(model_run_id=provided_uuid, description=description)
    try:
        DBSession.add(modelrun)
        DBSession.commit()
        DBSession.flush()
        DBSession.refresh(modelrun)
    except Exception as err:
        return HTTPServerError(err)
    geodatapath = '/geodata/watershed-data'
    first_two_of_uuid = dataset_uuid[:2]
    parent_dir = os.path.join(geodatapath, first_two_of_uuid)
    output_path = os.path.join(parent_dir, dataset_uuid)
    if not os.path.isdir(output_path):
        if not os.path.isdir(geodatapath):
            os.mkdir(geodatapath)
            if not os.path.isdir(parent_dir):
                os.mkdir(parent_dir)
        os.mkdir(output_path)
    return Response(dataset_uuid)

