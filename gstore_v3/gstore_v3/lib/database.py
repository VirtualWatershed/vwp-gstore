from ..models import DBSession
#from the generic model loader (like meta from gstore v2)
from ..models.datasets import Dataset

from ..models.tileindexes import *
from ..models.collections import Collection
from ..models.repositories import Repository
from ..models.apps import GstoreApp
from ..models.provenance import ProvOntology

from sqlalchemy import text

'''
object verification checks

'''    

def get_dataset(dataset_id, lean):
    """return Dataset by ID or UUID

    Args:
        dataset_id: integer ID or string UUID to query

    Returns:
        d (Dataset): returns the Dataset object or None   

    Raises:
        
    """
    try:
        dataset_id = int(dataset_id)
        clause = Dataset.id==dataset_id
    except:
        clause = Dataset.uuid==dataset_id

    if lean != 0:
        d = DBSession.query(Dataset).from_statement( text("SELECT uuid, model_run_uuid, model_run_name, description FROM datasets") ).filter(clause).first()
    else:
        d = DBSession.query(Dataset).filter(clause).first()
    return d
 
def get_tileindex(tile_id):
    """return TileIndex by ID or UUID

    Args:
        tile_id: integer ID or string UUID to query

    Returns:
        tile (TileIndex): returns the TileIndex object or None   

    Raises:
        
    """
    try:
        tile_id = int(tile_id)
        clause = TileIndex.id==tile_id
    except:
        clause = TileIndex.uuid==tile_id

    tile = DBSession.query(TileIndex).filter(clause).first()
    return tile

def get_collection(collection_id):    
    """return Collection by ID or UUID

    Args:
        collection_id: integer ID or string UUID to query

    Returns:
        collection (Collection): returns the Collection object or None   

    Raises:
        
    """
    try:
        collection_id = int(collection_id)
        clause = Collection.id==collection_id
    except:
        clause = Collection.uuid==collection_id

    collection = DBSession.query(Collection).filter(clause).first()
    return collection


def get_repository(repo_name):
    """return Repository by name

    Args:
        repo_name: repository name (string)

    Returns:
        repo (Repository): returns the Repository object or None   

    Raises:
        
    """
    clause = Repository.name.ilike(repo_name)
    repo = DBSession.query(Repository).filter(clause).first()
    return repo   

def get_app(app_key):    
    """return APP by key (short alias)

    Args:
        app_key: string for the key

    Returns:
        app (GstoreApp): returns the GstoreApp object or None   

    Raises:
        
    """
    clause = GstoreApp.route_key==app_key
    app = DBSession.query(GstoreApp).filter(clause).first()
    return app
        
