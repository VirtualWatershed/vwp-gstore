import pymongo
from urlparse import urlparse

class gMongo:
    """wrapper for the MongoDB methods.

    Note: 
        This will be updated once the mongo pooling connection is 
        in place.
    """

    #use the mongo connection widget instead
    def __init__(self, mongo_uri):
        """set up the MongoDB connection 

        Args:
            mongo_uri (gMongoUri): URI parser for our MongoDB connection strings

        Returns:
        
        Raises:
        
        """
        self.conn = pymongo.Connection(host=mongo_uri.hostname, port=mongo_uri.port)
        self.db = self.conn[mongo_uri.db]
        if mongo_uri.user and mongo_uri.password:
            #TODO: add some error handling here
            self.db.authenticate(mongo_uri.user, mongo_uri.password)
        self.collection = self.db[mongo_uri.collection_name]

    def set_collection(self, coll):
        """set the collection 

        Notes:
            This is not necessary if the collection is provided as part of the gMongoUri
            object.

        Args:
            coll (string): collection name

        Returns:
        
        Raises:
        
        """
        self.collection = self.db[coll]

    def close(self):
        """close the MongoDB connection 

        Args:
            
        Returns:
        
        Raises:
        
        """
        self.conn.close()

    #TODO: something about the possibly unknown collection info
    def query(self, querydict, fielddict={}, sortdict = {}, limit=None, offset=None):
        """Execute a mongo query

        Notes:
            This is limited and tailored to the kinds of vector queries
            currently in place. 

        Args:
           querydict (dict): the mongo query terms, for example {'d.id': 12345, 'f.id': 12976645}
           fielddict (dict, optional): the fields to return if not requesting the entire document
           sortdict (dict, optional): the fields and sort direction
           limit (int, optional): number of documents to return
           offset (int, optional): index of document to start with

        Returns:
            q {cursor}: the document result set
        
        Raises:
        
        """

        if fielddict:
            q = self.collection.find(querydict, fielddict)
        else:
            #do not use an empty fielddict -> it will only return the _id values
            q = self.collection.find(querydict)

        #1 = asc, -1 = desc
        if sortdict:
            q = q.sort(sortdict)

        if limit:
            offset = offset if offset else 0
            q = q.limit(limit).skip(offset)

        return q

    #TODO: this.
    def insert(self, docs):
        """Insert one or more documents

        Notes:
            Check that the mongo write didn't fail silently or 
            make sure that that option is disabled in the mongo
            config.

        Args:
           querydict (dict): the mongo query terms, for example {'d.id': 12345, 'f.id': 12976645}
           fielddict (dict, optional): the fields to return if not requesting the entire document
           sortdict (dict, optional): the fields and sort direction
           limit (int, optional): number of documents to return
           offset (int, optional): index of document to start with

        Returns:
            s {str}: an empty string or the error
        
        Raises:

        """
        
        try:
            self.collection.insert(docs)
        except Exception as err:
            return err
        return ''


    def remove(self, querydict):
        """Remove one or more documents based on a query

        Notes:

        Args:
           querydict (dict): the mongo query terms, for example {'d.id': 12345, 'f.id': 12976645}

        Returns:
            s {string}: succes or failure
        
        Raises:
        
        """
        done = self.collection.remove(querydict)        
        return done

class gMongoUri:
    """A basic parser for the MongoDB connection string

    Notes:
         
    
    """
    def __init__(self, connstr, collstr):
        """the parser

        Args:
           connstr (str): the connection string, from the config
           collstr (str): the collection to use

        Returns:
        
        Raises:
        
        """
        connection_uri = urlparse(connstr)
        self.collection_name = collstr
        self.hostname = connection_uri.hostname
        self.port = connection_uri.port
        self.db = connection_uri.path[1:]
        self.user = connection_uri.username if connection_uri.username else ''
        self.password = connection_uri.password if connection_uri.password else ''

    
