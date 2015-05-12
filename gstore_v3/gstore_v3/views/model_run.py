from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPServerError, HTTPBadRequest, HTTPUnprocessableEntity
from pyramid.security import Allow, Authenticated, remember, forget, authenticated_userid, unauthenticated_userid
from sqlalchemy import desc, asc, func
from sqlalchemy.sql.expression import and_, not_, cast
from sqlalchemy.sql import between
import sqlalchemy

import os, json, re
import requests
from xml.sax.saxutils import escape

from ..models import DBSession
from ..models.model_runs import (
    Modelruns,
    )
from ..models.users import (
    Users,
    )

from ..models.datasets import Dataset, Category
from ..models.sources import Source, SourceFile
from ..models.metadata import OriginalMetadata, DatasetMetadata
from ..models.categories import categories_datasets

from ..lib.mongo import gMongo, gMongoUri
from ..lib.utils import *
from ..lib.spatial import *
from ..lib.database import get_dataset

#**************************************************************************************************************************

def threddspermissioncheck():
    print "thredds test"
    query = DBSession.query(Modelruns.model_run_id).filter(Modelruns.public==True).all()
    #print query
    uuids = []
    for item in query:
        uuids.append(item[0])
    #print uuids
    for uuid in uuids:
        uuidstring = uuid.decode('utf-8')
        firsttwo = uuidstring[:2]
        path = '/geodata/thredds/%s' % firsttwo
        if not os.path.isdir(path):
            os.mkdir(path)
        linkname =  path + '/' + uuidstring
        sourcepath = '/geodata/watershed-data/' + firsttwo + '/' + uuidstring
        if not os.path.islink(linkname):
            os.symlink(sourcepath, linkname)
    
    query = DBSession.query(Modelruns.model_run_id).filter(Modelruns.public==False).all()
    uuids = []
    for item in query:
        uuids.append(item[0])
    #print uuids
    for uuid in uuids:
        uuidstring = uuid.decode('utf-8')
        firsttwo = uuidstring[:2]
        path = '/geodata/thredds/%s' % firsttwo
        #if not os.path.isdir(path):
        #    os.mkdir(path)
        if os.path.isdir(path):
            linkname =  path + '/' + uuidstring
            if os.path.islink(linkname):
                print 'unlinking %s' % linkname
                os.unlink(linkname)
            if os.listdir(path) == []:
                print 'removing %s' % path
                os.rmdir(path)

#**************************************************************************************************************************
        
@view_config(route_name='threddscheck', request_method='GET', permission='threddscheck')
def threddscheck(request):
    threddspermissioncheck()
    return Response('200')

#**************************************************************************************************************************

@view_config(route_name='edit_model_run', request_method='PUT', permission='add_model_run')
def edit_model_run(request):
    userid = authenticated_userid(request)
    model_run_uuid = request.params['model_run_uuid'].decode('utf-8')
    public =  request.params['public'] if 'public' in request.params else None
    full_model_query=DBSession.query(Modelruns.model_run_id,Modelruns.userid).filter((Modelruns.model_run_id==model_run_uuid) & (Modelruns.userid==userid)).first()
    userid_query=DBSession.query(Modelruns.userid).filter(Modelruns.userid==userid).first()
    uuid_query=DBSession.query(Modelruns.model_run_id).filter(Modelruns.model_run_id==model_run_uuid).first()

    if(full_model_query==None):
        if(userid_query==None):
            return HTTPUnprocessableEntity("The userid is not associated with any model runs")
        else:
            if(uuid_query==None):
                return HTTPUnprocessableEntity("The model run uuid is not located in the list of model runs")
            else:
                return HTTPUnprocessableEntity("The model run exists, but you are not the owner and cannot modify this model run")
    else:
        if public is not None:
            print public
            print model_run_uuid
            update = DBSession.query(Modelruns.public).filter(Modelruns.model_run_id==model_run_uuid).update({'public':public}) 
            threddspermissioncheck()
        return Response('200')    



#**************************************************************************************************************************

@view_config(route_name='check_model_id', request_method='POST', permission='add_model_run')
def check_model_id(request):
    modelid = request.params['modelid'].decode('utf-8')
    geodatapath = '/geodata/watershed-data'
    first_two_of_uuid = modelid[:2]
    parent_dir = os.path.join(geodatapath, first_two_of_uuid)
    sub_dir = os.path.join(parent_dir, modelid)
    #This should also check the DB to see if the model run exists, but I don't have the time right now. 
    if not os.path.isdir(sub_dir):
        return Response('False')
    return Response('True')    

#**************************************************************************************************************************

@view_config(route_name='add_model_id', request_method='POST', permission='add_model_run')
def add_model_id(request):
    userid = authenticated_userid(request)
    rn = DBSession.query(Users.firstname, Users.lastname).filter(Users.userid==userid).first()
    firstname = rn.firstname
    lastname = rn.lastname
    provided_uuid = generate_uuid4()
    dataset_uuid = str(provided_uuid)
    app = request.matchdict['app']
    description=request.json['description']
    researcher_name= firstname + " " + lastname
    model_run_name=request.json['model_run_name']
    model_keywords=request.json['model_keywords']
    public = request.json.get('public') if 'public' in request.json else True
    print userid
    modelrun = Modelruns(model_run_id=provided_uuid, description=description, researcher_name=researcher_name, model_run_name=model_run_name, model_keywords=model_keywords, userid=userid, public=public)
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
    if not os.path.isdir(geodatapath):
        os.mkdir(geodatapath)
    if not os.path.isdir(parent_dir):
        os.mkdir(parent_dir)
    if not os.path.isdir(output_path):
        os.mkdir(output_path)
    return Response(dataset_uuid)

#**************************************************************************************************************************

@view_config(route_name='delete_model_id', request_method='DELETE', permission='delete')
def delete_model_id(request):
    print "\nDelete_model_run() view called"
    app = request.matchdict['app']
    model_uuid=request.json['model_uuid']
    userid = authenticated_userid(request)

    print "\nModel run UUID passed in: %s\n" % model_uuid

    #First, test whether the passed model_run_uuid is even in the modelruns table
    full_model_query=DBSession.query(Modelruns.model_run_id,Modelruns.userid).filter((Modelruns.model_run_id==model_uuid) & (Modelruns.userid==userid)).first()
    userid_query=DBSession.query(Modelruns.userid).filter(Modelruns.userid==userid).first()
    uuid_query=DBSession.query(Modelruns.model_run_id).filter(Modelruns.model_run_id==model_uuid).first()
    
    if(full_model_query==None):
        if(userid_query==None):  
            return HTTPUnprocessableEntity("The userid is not associated with any model runs")            
        else:
            if(uuid_query==None):
                return HTTPUnprocessableEntity("The model run uuid is not located in the list of model runs")
            else:
                return HTTPUnprocessableEntity("The model run exists, but you are not the owner and cannot delete this model run")
    else:
            
	      print "\nModel Run UUID found in the database"
	      #first, pass in model_run_uuid, and determine whether the model run has children
	      model_query=DBSession.query(Dataset.id).filter((Dataset.parent_model_run_uuid==model_uuid) & (Dataset.model_run_uuid != Dataset.parent_model_run_uuid)).first()

	      #IF ANYTHING IS RETURNED TO data_query, THEN YOU CANNOT DELETE IT, AND MUST EXIT WITH ERROR, IF NOTHING IS RETURNED, THEN PROCEED TO DELETE THE DATASETS	

	      if not model_query:
			  print "No Children found ----> Deleting all datasets...with the specificed model_run_uuid : %s" % model_uuid
			  data_query=DBSession.query(Dataset.id,Dataset.uuid).filter(Dataset.model_run_uuid==model_uuid)

			  #Search through all of the datasets with matching model_run_uuid and grab the id and the dataset UUID
			  #then iterate through all records and run each of the delete commands for all of the tables
			  counter=0
			  print "\nDeleting records now..."
			  for row in data_query:
				  datasetID=row[0]
				  datasetUUID=row[1]
				  print "\nDeleting dataset with ID: %s and dataset UUID: %s" % (datasetID,datasetUUID)
				  counter+=1

				  #DELETE from gstoredata.source_files where source_id in (select id from gstoredata.sources where dataset_id = ####);
				  q=DBSession.query(Source.id).filter(Source.dataset_id==datasetID).subquery()
				  s=DBSession.query(SourceFile.source_id).filter(SourceFile.source_id.in_(q)).delete(synchronize_session='fetch')
				  DBSession.commit()

				  #DELETE from gstoredata.sources where dataset_id = 8765;
				  t=DBSession.query(Source.dataset_id).filter(Source.dataset_id==datasetID).delete()
				  DBSession.commit()
		  
				  #DELETE from gstoredata.metadata where dataset_id = 8765;
			          u=DBSession.query(DatasetMetadata.dataset_id).filter(DatasetMetadata.dataset_id==datasetID).delete()
				  DBSession.commit()
	  
				  #DELETE from gstoredata.original_metadata where dataset_id = 8765;
				  m=DBSession.query(OriginalMetadata.dataset_id).filter(OriginalMetadata.dataset_id==datasetID).delete()
				  DBSession.commit()
	  
				  #DELETE from gstoredata.projects_datasets where dataset_id = 8765;
				  #THERE ARE NO RECORDS IN THIS TABLE, SO IT APPEARS NOT TO BE WORKING FOR DATASET INSERTS

				  #DELETE from gstoredata.categories_datasets where dataset_id = 8765;
				  #This delete is called differently, because we are importing a table and NOT a class (e.g. categories_datasets from ../models/categories.py)
				  cd=categories_datasets.delete(categories_datasets.c.dataset_id==datasetID)
				  cd.execute()
	  
				  #DELETE from gstoredata.datasets where id = 8765;
				  d=DBSession.query(Dataset.id,Dataset.uuid).filter(Dataset.id==datasetID).delete()
				  DBSession.commit()

				  #Finally, delete dataset record from elasticSearch
				  es_root=request.registry.settings['es_root']
				  es_dataset_index=request.registry.settings['es_dataset_index']
				  es_dbuser=request.registry.settings['es_dbuser']
				  es_dbpass=request.registry.settings['es_dbpass']
				  #print "es_root:%s  es_dbuser:%s es_dbpass:%s  es_dataset_index:%s" % (es_root,es_dbuser,es_dbpass,es_dataset_index)
				  dbURL=os.path.join(es_root,es_dataset_index,"dataset",datasetUUID)
				  #print "dbURL: %s" % dbURL
				  r = requests.delete(dbURL, auth=(es_dbuser,es_dbpass))
				  print "Deleting from elasticSearch dataset no. %s with status code: %s" % (datasetID,r.status_code)

			  print "Datasets deleted: %s" % counter

			  #Now delete the model_run_uuid from the models table
			  y=DBSession.query(Modelruns.model_run_id).filter(Modelruns.model_run_id==model_uuid).delete()
			  DBSession.commit()
			  print "\nDeleting model run record from model_runs table......%s" % model_uuid
			  deletedModelRun="Deleted model run uuid: %s" % model_uuid
			  return Response(deletedModelRun)	

	      #if the model run has children equal to the passed model_run_uuid, then do nothing and exit
	      else:
			  print "Children FOUND.....cannot delete this model run"
			  return HTTPUnprocessableEntity("The requested model run has dependent children datasets and cannot be deleted")

