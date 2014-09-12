import os, re, zipfile
import hashlib

from sqlalchemy.sql.expression import and_
from sqlalchemy.sql import between

from datetime import datetime

import uuid
import urllib2

import subprocess


'''
image mimetypes (mostly for mapserver)
'''
_IMAGE_MIMETYPES = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'GIF': 'image/gif',
        'TIFF': 'image/tiff'
    }
def get_image_mimetype(s):
    """return the mimetype by image format

    Notes: 

    Args:
        s (str): the format to identify

    Returns:
        m (tuple): the format and mimetype if found or NONE
    
    Raises:
    
    """
    m = [(k, v) for k, v in _IMAGE_MIMETYPES.iteritems() if v.lower() == s.lower() or k.upper() == s.upper()]
    m = m[0] if m else None
    return m

'''
file utils
'''

def create_zip(fullname, files):
    """create a zipfile

    Notes:
        This does not respect the directory hierarchy of the files to include
        in the zip. So no nested paths in the output zip. 

    Args:
        fullname (str): path to the output zip file
        files (list): the files to include

    Returns:
        fullname (str): the fullname again
    
    Raises:
    
    """
    zipf = zipfile.ZipFile(fullname, mode='w', compression=zipfile.ZIP_STORED)
    for f in files: 
        fname = f.split('/')[-1]
        zipf.write(f, fname)
    zipf.close()

    #which is silly except as a success indicator
    #which is silly
    return fullname

'''
xslt/xml subprocess calls

'''
def transform_xml(xml, xslt_path, params):
    """saxonb-xslt transformation for in memory XML

    Notes:

    Args:
        xml (str): XML as string
        xslt_path (str): full path to the xslt file
        params (dict): dictionary of parameters used in the xslt

    Returns:
        output (str): the transformed xml
    
    Raises:
    
    """
    param_str = convert_to_xslt_params(params)

    cmd = 'saxonb-xslt -s:- -xsl:%s %s' % (xslt_path, param_str)
    
    s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output = s.communicate(input=xml.encode('utf-8'))[0]
    ret = s.wait()
    return output

def transform_xml_file(xml_path, xslt_path, params):
    """saxonb-xslt transformation for file-based xml

    Notes:

    Args:
        xml_path (str): full path to the xml file
        xslt_path (str): full path to the xslt file
        params (dict): dictionary of parameters used in the xslt

    Returns:
        output (str): the transformed xml
    
    Raises:
    
    """
    param_str = convert_to_xslt_params(params)

    cmd = 'saxonb-xslt -s:%s -xsl:%s %s' % (xml_path, xslt_path, param_str)
    
    s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    output = s.communicate()[0]
    ret = s.wait()
    return output

def validate_xml(xml):
    """StdInParse (xerces) validation for in memory xml

    Notes:
        schema must be defined in the xml before validation

    Args:
        xml (str): XML as string

    Returns:
        stderr (str): the validation response as string
    
    Raises:
    
    """
    
    cmd = 'StdInParse -v=always -n -s -f'
    s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    #we need stderr from pparse/stdinparse to actually catch the errors
    stdout, stderr = s.communicate(input=xml)
    ret = s.wait()
    return stderr

def convert_to_xslt_params(params):
    """convert a dict to saxonb parameter string

    Notes:

    Args:
        params (dict): dictionary of parameters used in the xslt

    Returns:
         (str): the kvp as space-delimited k=v 
    
    Raises:
    
    """
    return ' '.join(['%s=%s' % (p, params[p] if ' ' not in params[p] else '"%s"' % params[p]) for p in params])


'''
hashes
(see dataone api)
'''
def generate_hash(zipfile, algo):
    """generate the hash (SHA-1 or MD5) for a zip file

    Notes:
        This is generally for DataONE support.

    Args:
        zipfile (str): file path for the zip
        algo (str): name of the algorithm to use 

    Returns:
        (str): the hash
    
    Raises:
    
    """
    #TODO: change this if dataone rolls out other hash types or we want something else
    m = hashlib.md5() if algo.lower() == 'md5' else hashlib.sha1()
    zf = open(zipfile, 'rb')
    #turn this on if the files are too big for memory
    while True:
        data = zf.read(2**20)
        if not data:
            break
        m.update(data)
    zf.close()
    return m.hexdigest()

'''
uuid4 generator
'''
def generate_uuid4():
    """generate a UUID4 

    Notes:

    Args:

    Returns:
        (str):the uuid
    
    Raises:
    
    """
    return str(uuid.uuid4())

'''
regex

'''
def match_pattern(pattern, test):
    """regex match pattern

    Notes:
        Mostly for valid uuids

    Args:
        pattern (str): the pattern to use
        test (str): the str to check

    Returns:
        (bool): True if any match was found
    
    Raises:
    
    """
    p = re.compile(pattern)
    results = p.match(test)

    return results is not None


'''
gstore default lists
'''
def get_all_formats(req):
    """get the default formats from the config

    Notes:

    Args:
        req (Request): the request object from the view

    Returns:
        (list): the list of default formats from the config
    
    Raises:
    
    """
    fmts = req.registry.settings['DEFAULT_FORMATS']
    if not fmts:
        return []
    return fmts.split(',')
    
def get_all_services(req):    
    """get the default services from the config

    Notes:

    Args:
        req (Request): the request object from the view

    Returns:
        (list): the list of default services from the config
    
    Raises:
    
    """
    svcs =  req.registry.settings['DEFAULT_SERVICES']
    if not svcs:
        return []
    return svcs.split(',')

def get_all_repositories(req):
    """get the default repositories from the config

    Notes:

    Args:
        req (Request): the request object from the view

    Returns:
        (list): the list of default repositories from the config
    
    Raises:
    
    """
    repos =  req.registry.settings['DEFAULT_REPOSITORIES']
    if not repos: 
        return []
    return repos.split(',')

def get_all_standards(req):
    """get the default documentation standards from the config

    Notes:
        Excludes the GSTORE standard.

    Args:
        req (Request): the request object from the view

    Returns:
        (list): the list of default standards from the config
    
    Raises:
    
    """
    stds = req.registry.settings['DEFAULT_STANDARDS']
    if not stds:
        return []
    return [s for s in stds.split(',') if s != 'GSTORE']


'''
build standard route urls (ogc services, metadata services, dataset downloads)
'''
def build_ogc_url(app, data_type, uuid, service, version):
    """build the OGC service URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        The route: /apps/{app}/{type}/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/services/{service_type}/{service}
        The query params: ?SERVICE={service}&REQUEST=GetCapabilities&VERSION={version}

    Args:
        app (str): application key
        data_type (str): data object type (datasets, collections, etc)
        uuid (str): uuid of the data object
        service (str): ogc service abbreviation (wms, wfs, wcs)
        version (str): the version of the OGC service

    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/%s/%s/services/%s/%s?SERVICE=%s&REQUEST=GetCapabilities&VERSION=%s' % (app, data_type, uuid, 'ogc', service, service, version) 


def build_metadata_url(app, data_type, uuid, standard, extension):
    """build the Documentation/metadata service URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        The route: /apps/{app}/{datatype}/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/metadata/{standard}.{ext}

    Args:
        app (str): application key
        data_type (str): data object type (datasets, collections, etc)
        uuid (str): uuid of the data object
        standard (str): documentation standard (see supported standards for list)
        extension (str): the output file extension (xml, html, etc)

    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/%s/%s/metadata/%s.%s' % (app, data_type, uuid, standard, extension)

def build_dataset_url(app, uuid, basename, aset, extension):
    """build the dataset download URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        The route: /apps/{app}/datasets/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/{basename}.{type}.{ext}

    Args:
        app (str): application key
        uuid (str): uuid of the dataset
        basename (str): dataset basename
        aset (str): original or derived
        extension (str): the output file extension

    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/datasets/%s/%s.%s.%s' % (app, uuid, basename, aset, extension)

def build_service_url(app, data_type, uuid):
    """build the data object service description URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        The route: /apps/{app}/{data_type}/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/services.json

    Args:
        app (str): application key
        data_type (str): data object type (datasets, collections, etc)
        uuid (str): uuid of the data object
        
    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/%s/%s/services.json' % (app, data_type, uuid)
    
def build_mapper_url(app, uuid):
    """build the dataset mapper URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        This will be deprecated when the mapper is.

        The route: /apps/{app}/datasets/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/mapper

    Args:
        app (str): application key
        uuid (str): uuid of the dataset
        
    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/datasets/%s/mapper' % (app, uuid)

def build_prov_trace_url(app, uuid, ontology, format):
    """build the dataset provenance trace URL

    Notes:
        This doesn't use the Pyramid app's host (or route_path/route_url).
        This version's proxy widget only works with traversal (not enabled outside of D1 routes).
        Prepend the host or load balancer URL as needed.

        This doesn't get the provenance data series base. It might.

        The route: /apps/{app}/datasets/{id:\d+|[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}}/prov/{ontology}.{ext}

    Args:
        app (str): application key
        uuid (str): uuid of the dataset
        ontology (str): name of the ontology used in the trace
        format (str): uuid of the dataset
        
    Returns:
        (str): the generated string
    
    Raises:
    
    """
    return '/apps/%s/datasets/%s/prov/%s.%s' % (app, uuid, ontology, format)
    
def normalize_params(params):
    """normalize all of the query parameter keys to lower case

    Notes:
        
    Args:
        params (dict): query parameter kvp
        
    Returns:
        (dict): query params with lower case keys
    
    Raises:
    
    """
    new_params = {}
    for k in params.keys():
        new_params[k.lower()] = params[k]
    return new_params 

def decode_params(params):
    """decode the query parameters (see D1 testing)

    Notes:
        
    Args:
        params (dict): query parameter kvp
        
    Returns:
        (dict): query params with everything decoded
    
    Raises:
    
    """
    new_params = {}
    for k in params.keys():
        new_params[urllib2.unquote(urllib2.unquote(k.lower()).decode('unicode_escape'))] = urllib2.unquote(urllib2.unquote(params[k]).decode('unicode_escape')) 
    return new_params


'''
datetime utils
'''
def convert_timestamp(in_timestamp):
    """convert timestamp string to datetime

    Notes:
        Timestamp as yyyyMMdd{THHMMss} with the time component optional
        
    Args:
        in_timestamp (str): timestamp to convert
        
    Returns:
        (datetime): parsed timestamp or None
    
    Raises:
    
    """
    sfmt = '%Y%m%dT%H:%M:%S'
    if not in_timestamp:
        return None
    try:
        if 'T' not in in_timestamp:
            in_timestamp += 'T00:00:00'
        out_timestamp = datetime.strptime(in_timestamp, sfmt)
        return out_timestamp
    except:
        return None
        
def get_single_date_clause(column, start_range, end_range):
    """build a sqla datetime clause for a single column

    Notes:
        Timestamps as yyyyMMdd{THHMMss} with the time component optional
        Handles greater than equal, less than equal, or BETWEEN
        
    Args:
        column (Column): column object to query
        start_range (str): timestamp for the start of the query range
        end_range (str): timestamp for the end of the query range
        
    Returns:
        (Clause): the generated sqla clause
    
    Raises:
    
    """
    start_range = convert_timestamp(start_range)
    end_range = convert_timestamp(end_range)

    if start_range and not end_range:
        clause = column >= start_range
    elif not start_range and end_range:
        clause = column < end_range
    elif start_range and end_range:
        clause = between(column, start_range, end_range)
    else:
        clause = None
    return clause
    
#to compare two sets of date ranges, one in table and one from search
def get_overlap_date_clause(start_column, end_column, start_range, end_range):
    """build a sqla datetime clause for two columns

    Notes:
        Timestamps as yyyyMMdd{THHMMss} with the time component optional
        Handles greater than equal START COLUMN, less than equal END COLUMN, or BETWEEN
        
    Args:
        start_column (Column): column object to query
        end_column (Column): column object to query
        start_range (str): timestamp for the start of the query range
        end_range (str): timestamp for the end of the query range
        
    Returns:
        (Clause): the generated sqla clause
    
    Raises:
    
    """
    start_range = convert_timestamp(start_range)
    end_range = convert_timestamp(end_range)

    if start_range and not end_range:
        clause = start_column >= start_range
    elif not start_range and end_range:
        clause = end_column < end_range
    elif start_range and end_range:
        clause = and_(start_column <= end_range, end_column >= start_range)
    else:
        clause = None
    return clause
    
