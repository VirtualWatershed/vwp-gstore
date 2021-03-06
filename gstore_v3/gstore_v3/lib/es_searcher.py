import requests
from ..lib.spatial import *
from ..lib.utils import convert_timestamp, convert_datetimestamp

from gstore_v3.models import Base, DBSession
from sqlalchemy import func

import json

from requests.auth import HTTPBasicAuth

class EsSearcher():
    """ElasticSearch search api access

    Note:
        See EsIndexer for indexing access.
        
    Attributes:
        query_data (dict): search filters for the ES POST request
        results (dict): request response
        dfmt (str): basic date format
        srid (int): default spatial ref for the bbox filter
        default_limit (int): defaults to 14
        default_offset (int): defaults to 0
        default_fields (list): list of field names to include in the response (defaults to _id, our uuids, only)
    """
    
    query_data = {} 
    results = {} 

    dfmt = '%Y-%m-%d'
    dtfmt = '%Y-%m-%d %H:%M:%S'
    srid = 4326
    default_limit = 15
    default_offset = 0
    default_fields = ["_id"] 
    
    def __init__(self, es_description):
        """set up the elasticsearch POST url

        Notes:
            "type" in the es_description can be a comma-delimited list of objects types (datasets,collections)
            
        Args:
            es_description (dict): host, index, type, user, password
                    
        Returns:
        
        Raises:
        """
        self.es_description = es_description 

        self.es_url = es_description['host'] + es_description['index'] + '/' + es_description['type'] + '/_search'
        self.user = es_description['user']
        self.password = es_description['password']

    def __repr__(self):
        return '<EsSearcher (%s)>' % (self.es_url)

    def get_query(self):
        """return the search filters 

        Notes:
            For testing purposes
            
        Args:
                    
        Returns:
            (dict): the search filters
        
        Raises:
        """
        return self.query_data

    def get_result_total(self):
        """return the number of objects returned by the filter

        Notes:
            
        Args:
                    
        Returns:
            (int): the total number of objects found for the filter(s)
        
        Raises:
        """ 
        return self.results['hits']['total'] if 'hits' in self.results else 0

    def get_result_ids(self):
        """return the _id and object type for the result set

        Notes:
            Used to generate the output from the object models (services description)
            
        Args:
                    
        Returns:
            (list): list of tuples (_id, _type)
        
        Raises:
        """
        if not self.results:
            return []        
        
        return [(i['_id'], i['_type']) for i in self.results['hits']['hits']]

    def search(self):
        """execute the es request

        Notes:
            
        Args:
                    
        Returns:
            (json): the json response from elasticsearch
        
        Raises:
            Exception: returns the es error if the status code isn't 200
        """
        testdata=json.dumps(self.query_data)
        results = requests.post(self.es_url, data=json.dumps(self.query_data), auth=(self.user, self.password))
        if results.status_code != 200:
            self.results = {}
            raise Exception(results.text)

        self.results = results.json()
        return self.results

    def parse_basic_query(self, app, query_params, exclude_fields=[], available_uuids=[]):

        """build the search filter dict 

        Notes:
            
        Args:
            app (str): the app key alias
            query_params (dict): the query params from the gstore search request
            exclude_fields (list, optional): list of fields to use for MISSING query (see collections)
                    
        Returns:
        
        Raises:
        """
        #pagination
        limit = int(query_params['limit']) if 'limit' in query_params else self.default_limit
        offset = int(query_params['offset']) if 'offset' in query_params else self.default_offset


        #category
        theme, subtheme, groupname = self.extract_category(query_params)


        #keywords
        keyword = query_params.get('query', '').replace('+', '')


        #date added
        start_added = query_params.get('start_time', '')
        start_added_date = convert_timestamp(start_added)
        end_added = query_params.get('end_time', '')
        end_added_date = convert_timestamp(end_added)

        #valid dates
        start_valid = query_params.get('timestamp_start', '')
        start_valid_date = convert_datetimestamp(start_valid)
        empty = ""

        end_valid = query_params.get('timestamp_end', '')
        end_valid_date = convert_datetimestamp(end_valid)

	#model run UUID
        model_run_uuid = query_params.get('model_run_uuid', '')

        #model run name
        model_run_name = query_params.get('model_run_name', '') 

        #model_var
        model_vars = query_params.get('model_vars', '')

        #parent model run UUID
        parent_model_run_uuid = query_params.get('parent_model_run_uuid', '')

        #model set (input output analytic)
        model_set = query_params.get('model_set', '')

        #external user UUID
        externaluserid = query_params.get('externaluserid', '')
        #external app
        externalapp = query_params.get('externalapp', '')
        #model set type (raw binary and vis)
        model_set_type = query_params.get('model_set_type', '')

        #model set type (raw binary and vis)
        model_set_taxonomy = query_params.get('model_set_taxonomy', '')

        #formats/services/data type
        format = query_params.get('format', '')
        taxonomy = query_params.get('taxonomy', '')
        geomtype = query_params.get('geomtype', '').replace('+', ' ')
        service = query_params.get('service', '')
        duuid =  query_params.get('uuid', '')
        #spatial search
        box = query_params.get('box', '')
        epsg = query_params.get('epsg', '')


        #sorting
        sort = query_params.get('sort', 'lastupdate')
        if sort not in ['lastupdate', 'description', 'geo_relevance']:
            raise Exception('Bad sort')
        sort = 'date_added' if sort == 'lastupdate' else ('title_search' if sort == 'description' else sort)

        order = query_params.get('dir', 'desc').lower()
        if order not in ['asc', 'desc']:
            raise Exception('bad order')

        #set up the es sorting
        #TODO: how to handle multiple doctypes for the sorting
        #use title_search (not_analyzed) field for sorting. otherwise, it will parse the string
        # and sort on something that is not what we intend (ie. sort on 2013 at the end of the string rather
        # than the starting from the first word of the string)
        sort_arr = [{sort: {"order": order.lower()}}]
        if sort != 'title_search':
            #add a secondary sort for the title
            sort_arr.append({"title_search": {"order": "asc"}})
            
        sorts = {"sort": sort_arr}

        #build the json data
        query_request = {"size": limit, "from": offset, "fields": self.default_fields}

        # the main query block
        filtered = {}

        #all of the filters
        ands = [
            {"term": {"applications": app.lower()}},
            {"term": {"embargo": False}},
            {"term": {"active": True}}
        ]

        spatial_search = False        

        if theme:
            ands.append({"query": {"match": {"category.theme": {"query": theme, "operator": "and"}}}})
        if subtheme:
            ands.append({"query": {"match": {"category.subtheme": {"query": subtheme, "operator": "and"}}}})
        if groupname:
            ands.append({"query": {"match": {"category.groupname": {"query": groupname, "operator": "and"}}}})
        if format:
            ands.append({"query": {"term": {"formats": format.lower()}}})
        if service:
            ands.append({"query": {"term": {"services": service.lower()}}})
        if taxonomy:
            ands.append({"query": {"term": {"taxonomy": taxonomy.lower()}}})
        if model_run_uuid:
            ands.append({"query": {"term": {"model_run_uuid": model_run_uuid.lower()}}})
        if model_run_name:
            ands.append({"query": {"match": {"model_run_name": {"query": model_run_name, "operator": "and"}}}})
        if model_vars:
            ands.append({"query": {"term": {"model_vars": model_vars.lower()}}})
        if parent_model_run_uuid:
            ands.append({"query": {"term": {"parent_model_run_uuid": parent_model_run_uuid.lower()}}})
        if externaluserid:
            ands.append({"query": {"term": {"externaluserid": externaluserid.lower()}}})
        if externalapp:
            ands.append({"query": {"term": {"externalapp": externalapp.lower()}}})
        if model_set:
            ands.append({"query": {"term": {"model_set": model_set.lower()}}})
        if model_set_type:
            ands.append({"query": {"term": {"model_set_type": model_set_type.lower()}}})
        if model_set_taxonomy:
            ands.append({"query": {"term": {"model_set_taxonomy": model_set_taxonomy.lower()}}})
#hb
        if duuid:
            ands.append({"query": {"term": {"_id": duuid.lower()}}})


            #NOTE: geomtype is not currently in the indexed docs
            if geomtype and geomtype.upper() in ['POLYGON', 'POINT', 'LINESTRING', 'MULTIPOLYGON', '3D POLYGON', '3D LINESTRING']:
                ands.append({"query": {"term": {"geomtype": geomtype.lower()}}})
        if keyword:
            keyword_query = self.build_keyword_filter(keyword, ['aliases', 'title'])
            if keyword_query:
                ands.append(keyword_query)
        if box:
            geo_shape, search_area = self.build_geoshape_filter(box, epsg)

            ands.append(geo_shape)

            #override the default sort query
            sorts = {"sort": [{"_score": order.lower()}]}
            spatial_search = True

        if start_added_date or end_added_date:
            range_query = self.build_date_filter('date_added', start_added_date, end_added_date)
            if range_query:
                ands.append(range_query)
#Bill and Hays repaired this crap.

#        if start_valid_date or end_valid_date:
#            #TODO: this is not the right element name for the indexes
#            range_query = self.build_date_filter('valid_dates', start_valid_date, end_valid_date)
#            if range_query:
#                ands.append(range_query)

        if start_valid_date:
            range_query = self.build_date_time_filter('valid_start.date', start_valid_date, empty)
            if range_query:
                ands.append(range_query)

        if end_valid_date:
            range_query = self.build_date_time_filter('valid_end.date', empty, end_valid_date)
            if range_query:
                ands.append(range_query)

        if exclude_fields:
            #lazy man's handling of give me all collections (no collections in mapping) or any dataset not in a collection (in collection, has collections list in mapping)
            ands += [{"missing": {"field": e}} for e in exclude_fields]

        if len(available_uuids) > 0:
            shoulds = []
            for item in available_uuids:
                shoulds.append({ "match" : { "model_run_uuid" : item } })
            ands.append({"query" : {"bool" : {"should" : shoulds} } })


        if ands:
            filtered.update({"filter": {"and": ands}})

        if spatial_search:
            rescorer = {
                "custom_score": {
                    "query": {
                        "filtered": filtered
                    },
                    "params": {
                        "search_area": search_area
                    },
                    "script": "doc['area'].value / search_area"
                }
            }

            query_request.update({"query": rescorer})
        else:
            query_request.update({"query": {"filtered": filtered}})

        #and add the sort element back in
        query_request.update(sorts)
        #should have a nice es search
        self.query_data = query_request


    '''
    parse helpers
    '''

    #TODO: change this to handle the new hierarchy
    def extract_category(self, query_params):
        """parse the category triplet for the search 

        Notes:
            
        Args:
            query_params (dict): the query params from the gstore search request
                    
        Returns:
            theme (str): the theme
            subtheme (str): the subtheme
            groupname (str): the groupname
        
        Raises:
        """
        theme = query_params['modelname'].replace('+', ' ') if 'modelname' in query_params else ''
        subtheme = query_params['state'].replace('+', ' ') if 'state' in query_params else ''

#        theme = query_params['theme'].replace('+', ' ') if 'theme' in query_params else ''
 #       subtheme = query_params['subtheme'].replace('+', ' ') if 'subtheme' in query_params else ''

        #groupname = query_params['groupname'].replace('+', ' ') if 'groupname' in query_params else ''
        groupname = query_params['location'].replace('+', ' ') if 'location' in query_params else ''


        return theme, subtheme, groupname

    '''
    build helpers
    '''
    def build_date_time_filter(self, element, start_date, end_date):
        if not start_date and not end_date:
            return {}

        range_query = {}
        if start_date and not end_date:
            range_query = {"gte": start_date.strftime(self.dtfmt)}
        if not start_date and end_date:
            range_query = {"lte": end_date.strftime(self.dtfmt)}
        if start_date and end_date:
            range_query = {"gte": start_date.strftime(self.dtfmt), "lte": end_date.strftime(self.dtfmt)}
        return {"range": {element: range_query}}

    def build_date_filter(self, element, start_date, end_date):
        """build a date filter for an element 

        Notes:
            greater than equal, less than equal, between
            
        Args:
            element (str): name of the element for the date range filter
            start_date (str): date string a yyyy-MM-dd
            end_date (str): date string a yyyy-MM-dd
                    
        Returns:
            (dict): a range filter element
        
        Raises:
        """
        if not start_date and not end_date:
            return {}

        range_query = {}
        if start_date and not end_date:
            range_query = {"gte": start_date.strftime(self.dfmt)}
        if not start_date and end_date:
            range_query = {"lte": end_date.strftime(self.dfmt)}
        if start_date and end_date:
            range_query = {"gte": start_date.strftime(self.dfmt), "lte": end_date.strftime(self.dfmt)}
        return {"range": {element: range_query}}


    def build_geoshape_filter(self, box, epsg):
        """build a geometry filter for the location element 

        Notes:
            the geo relevance scoring is handling in the main search parser
            
        Args:
            box (str): bbox as minx,miny,maxx,maxy string
            epsg (str): epsg code
                    
        Returns:
            geo_shape (dict): a geoshape filter element
            search_area (float): area of the geometry (for the rescorer)
        
        Raises:
        """

        epsg = int(epsg) if epsg else self.srid

        bbox = string_to_bbox(box)
        bbox_geom = bbox_to_geom(bbox, epsg)

        if epsg != self.srid:
            reproject_geom(bbox_geom, epsg, self.srid)

        search_area = bbox_geom.GetArea()
        coords = [[[bbox[0], bbox[1]],[bbox[0],bbox[3]],[bbox[2],bbox[3]],[bbox[2],bbox[1]],[bbox[0],bbox[1]]]]

        geo_shape = {
            "geo_shape": 
            {
                "location.bbox" : {
                    "shape": {
                        "type": "Polygon",
                        "coordinates": coords
                    }
                }
            }
        }

        return geo_shape, search_area

    def build_keyword_filter(self, keywords, elements):
        """build a keyword filter for ORs across one or more elements 

        Notes:
            
        Args:
            keywords (str): the keyword string (phrase, etc)
            elements (list): list of elements to include in the search
                    
        Returns:
            (dict): an OR filter element
        
        Raises:
        """
        ors = [{"query": {"match": {element: {"query": keywords, "operator": "and"}}}} for element in elements]

        #TODO: add the wildcard search:
        '''
        {
            "sort": [{"title_search": {"order": "desc"}}],
            "fields": ["_id"],
            "query": {"filtered": {"filter": {"and": [
                {"term": {"applications": "rgis"}},
                {"term": {"embargo": false}},
                {"term": {"active": true}},
                {"query": {"wildcard": {"title_search":"Surfa*"}}}
                
            ]}}},
            "from": 0,
            "size": 15
        }
        '''
        
        return {
            "query": {
                "filtered": {
                    "filter": {
                        "or": ors
                    }
                }
            }
        }


class CollectionWithinSearcher(EsSearcher):
    """Additional ES search capability for "search within collection" 

    Note:
        Use the dataset doctype when instantiating.
        Don't include the exclude_fields (or leave out collections)

        Execute update_collection_filter between parsing the query and executing the search
        
    Attributes:
    """
    def update_collection_filter(self, collection_uuid):
        """add a filter to include the collection uuid to search within 

        Notes:
            
        Args:
            collection_uuid (str): the collection uuid to search within
                    
        Returns:
        
        Raises:
        """

        if not self.query_data:
            return ''

        '''
        as query.filtered.filter.and

        OR

        query.custom_score.query.filtered.filter.and

        '''

        #so we don't want any of the missing fields (def not missing collections, we need that now)

        uuid_filter = {"query": {"match": {"collections": collection_uuid}}}

        if 'custom_score' in self.query_data['query']:
            self.query_data['query']['custom_score']['query']['filtered']['filter']['and'].append(uuid_filter)
        else:
            self.query_data['query']['filtered']['filter']['and'].append(uuid_filter)
        
        

'''
>>> from gstore_v3.lib import es_searcher
>>> ed = {"host": "http://:/", "index": "", "type": "dataset,collection", "user": "", "password": ""}
>>> es = es_searcher.EsSearcher(ed)
>>> es.es_url
>>> qp = {"query": "modis"}
>>> es.parse_basic_query('rgis', qp, ['collections'])
>>> es.search()
>>> es.get_result_total()
'''

#for the repository search (object in repository?)
class RepositorySearcher(EsSearcher):
    """Additional ES search capability for repository listings 

    Note:
        
    Attributes:
    """
    query_data = {} 
    results = {} 

    dfmt = '%Y-%m-%d' 
    srid = 4326
    default_limit = 20
    default_offset = 0
    default_fields = ["_id"] 
    
    def __init__(self, es_description):
        self.es_description = es_description 

        self.es_url = es_description['host'] + es_description['index'] + '/' + es_description['type'] + '/_search'
        self.user = es_description['user']
        self.password = es_description['password']

    def __repr__(self):
        return '<RepositorySearcher (%s)>' % (self.es_url)

    def get_query(self):
        """return the search filters 

        Notes:
            For testing purposes
            
        Args:
                    
        Returns:
            (dict): the search filters
        
        Raises:
        """
        return self.query_data

    def get_result_total(self):
        """return the number of objects returned by the filter

        Notes:
            
        Args:
                    
        Returns:
            (int): the total number of objects found for the filter(s)
        
        Raises:
        """ 
        return self.results['hits']['total'] if 'hits' in self.results else 0

    def get_result_ids(self):
        """return the _id and object type for the result set

        Notes:
            Used to generate the output from the object models (services description)
            
        Args:
                    
        Returns:
            (list): list of tuples (_id, _type)
        
        Raises:
        """
        if not self.results:
            return []        
        
        return [(i['_id'], i['_type']) for i in self.results['hits']['hits']]

    def search(self):
        """execute the es request

        Notes:
            
        Args:
                    
        Returns:
            (json): the json response from elasticsearch
        
        Raises:
            Exception: returns the es error if the status code isn't 200
        """

        results = requests.post(self.es_url, data=json.dumps(self.query_data), auth=(self.user, self.password))
        if results.status_code != 200:
            self.results = {}
            raise Exception(results.text)

        self.results = results.json()
        
        #return the json
        return self.results

    def build_basic_search(self, app, repo, standard, query_params={}):
        """build the search filter dict 

        Notes:
            the query_params is not the straight request params obj. it's repacked to be clear about the date search
            
        Args:
            app (str): the app key alias
            repo (str): the repository alias
            standard (str): the documentation standard
            query_params (dict): the query params from the gstore search request
                    
        Returns:
        
        Raises:
        """

        query_request = {"size": self.default_limit, "from": self.default_offset, "fields": self.default_fields}

        ands = []

        repo_query = {
            "query": {
                "filtered": {
                    "filter": {
                        "nested": {
                            "path": "supported_repositories",
                            "filter": {
                                "and": [
                                    {"term": {"repos": repo}},
                                    {"term": {"app": app}}
                                ]
                            }
                        }
                    }
                }
            }
        }
        ands.append(repo_query)

        app_query = {
            "query": {
                "match": {"applications": app}
            }
        }
        ands.append(app_query)

        #TODO: change this to standard once the doc has been updated for it
        standards_query = {
            "query": {
                "match": {"standards": standard}
            }
        }
        ands.append(standards_query)

        #now the optional query params (basically the date searches)
        if query_params:

            metadata_query = query_params['metadata_date'] if 'metadata_date' in query_params else {}
            if metadata_query:
                '''
                changed: {order: date:}
                added: {order: date:}
                combination: and | or
                '''
                changed = metadata_query['changed'] if 'changed' in metadata_query else {}
                added = metadata_query['added'] if 'added' in metadata_query else {}

                mq = {}
                if changed and not added:
                    #basic range filter on metadata data
                    range_order = changed['order']
                    range_date = changed['date']
                    mq = self.build_date_filter('gstore_metadata.date', None, range_date) if range_order == 'before' else self.build_date_filter('gstore_metadata.date', range_date, None)
                elif not changed and added:
                    #basic range filter on date added or published?
                    range_order = added['order']
                    range_date = added['date']
                    mq = self.build_date_filter('date_added', None, range_date) if range_order == 'before' else self.build_date_filter('date_added', range_date, None)
                elif changed and added:
                    #combined range filter either AND or OR
                    combos = []
                    range_order = changed['order']
                    range_date = changed['date']
                    mq = self.build_date_filter('gstore_metadata.date', None, range_date) if range_order == 'before' else self.build_date_filter('gstore_metadata.date', range_date, None)
                    combos.append(mq)

                    range_order = added['order']
                    range_date = added['date']
                    mq = self.build_date_filter('date_added', None, range_date) if range_order == 'before' else self.build_date_filter('date_added', range_date, None)
                    combos.append(mq)

                    key = metadata_query['combination'].lower()

                    mq = {
                        "query": {
                            "filtered": {
                                "filter": {
                                    key: combos
                                }
                            }
                        }
                    }
                    
                if mq:
                    ands.append(mq) 


        query_request.update({"query": {"filtered": {"filter": {"and": ands}}}})

        self.query_data = query_request


    #TODO: this
    def build_search(self):
        '''search within a repo
        '''
        pass

        
