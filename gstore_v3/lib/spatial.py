from osgeo import ogr, osr
from datetime import datetime

from pyramid.wsgi import wsgiapp

from xml.sax.saxutils import escape, unescape

'''
the ogr field constants
'''

#just to have the integer values explicitly defined somewhere
_FIELD_TYPES = [
    (ogr.OFTInteger, 'integer', 0),
    (ogr.OFTIntegerList, 'integer list', 1),
    (ogr.OFTReal, 'double precision', 2),
    (ogr.OFTRealList, 'double precision list', 3),
    (ogr.OFTString, 'varchar', 4),
    (ogr.OFTStringList, 'varchar list', 5),
    (ogr.OFTWideString, 'text', 6),
    (ogr.OFTWideStringList, 'text list', 7),
    (ogr.OFTBinary, 'bytea', 8),
    (ogr.OFTDate, 'date', 9),
    (ogr.OFTTime, 'time', 10),
    (ogr.OFTDateTime, 'datetime', 11)
]

_GEOM_TYPES = [
    ('POINT', ogr.wkbPoint),
    ('LINESTRING', ogr.wkbLineString),
    ('POLYGON', ogr.wkbPolygon),
    ('MULTIPOINT', ogr.wkbMultiPoint),
    ('MULTILINESTRING', ogr.wkbMultiLineString),
    ('MULTIPOLYGON', ogr.wkbMultiPolygon),
    ('GEOMETRYCOLLECTION', ogr.wkbGeometryCollection),
    ('3D LINESTRING', ogr.wkbLineString25D),
    ('3D MULTILINESTRING', ogr.wkbMultiLineString25D),
    ('3D MULTIPOINT', ogr.wkbMultiPoint25D),
    ('3D MULTIPOLYGON', ogr.wkbMultiPolygon25D),
    ('3D POINT', ogr.wkbPoint25D),
    ('3D POLYGON', ogr.wkbPolygon25D)
]

_FILE_TYPES = [
    ('kml', 'KML', 'Keyhole Markup Language'),
    ('csv', 'CSV', 'Comma Separated Value'),
    ('gml', 'GML', 'Geographic Markup Language'),
    ('shp', 'ESRI Shapefile', 'ESRI Shapefile'),
    ('geojson', 'GeoJSON', 'Geographic Javascript Object Notation'),
    ('sqlite', 'SQLite', 'SQLite/SpatiaLite'),
    ('georss', 'GeoRSS', 'GeoRSS')
]

#for metadata reference
_FORMATS = {
    "tif": "Tagged Image File Format (TIFF)",
    "sid": "Multi-resolution Seamless Image Database (MrSID)",
    "ecw": "ERDAS Compressed Wavelets (ecw)",
    "img": "ERDAS Imagine (img)",
    "zip": "ZIP",
    "shp": "ESRI Shapefile (shp)",
    "kml": "KML",
    "gml": "GML",
    "geojson": "GeoJSON",
    "json": "JSON",
    "csv": "Comma Separated Values (csv)",
    "xls": "MS Excel format (xls)",
    "xlsx": "MS Office Open XML Spreadsheet (xslx)",
    "pdf": "PDF",
    "doc": "MS Word format (doc)",
    "docx": "MS Office Open XML Document (docx)",
    "html": "HTML",
    "txt": "Plain Text",
    "dem": "USGS ASCII DEM (dem)"
}

'''
type lookups
'''
def ogr_to_psql(ogr_type):
    """get the database type from the ogr field type

    Notes:
        
    Args:
        ogr_type (OGR.FIELDTYPE): int enum of the ogr field type
        
    Returns:
        (str): the database type
    
    Raises:
    """
    t = [g[1] for g in _FIELD_TYPES if g[0] == ogr_type]
    t = t[0] if t else 'varchar'
    return t

def psql_to_ogr(psql):
    """get the ogr type from the database field type

    Notes:
        
    Args:
        psql (str): database field type
        
    Returns:
        (ORG.FIELDTYPE): int enum of the ogr field type
    
    Raises:
    """
    t = [g[0] for g in _FIELD_TYPES if g[1] == psql]
    t = t[0] if t else ogr.OFTString
    return t

def format_to_filetype(format):
    """get the ogr file type

    Notes:
        
    Args:
        format (str): file format
        
    Returns:
        (str): ogr file type
    
    Raises:
    """
    f = [f[1] for f in _FILE_TYPES if f[0] == format]
    f = f[0] if f else None
    return f

def postgis_to_ogr(postgis):
    """get the geometry type

    Notes:
        
    Args:
        postgis (str): geometry type
        
    Returns:
        (ORG.GEOMTYPE): int enum of the ogr geometry type
    
    Raises:
    """
    t = [g[1] for g in _GEOM_TYPES if g[0] == postgis]
    t = t[0] if t else ogr.wkbUnknown
    return t

#get the metadata file format
def format_to_definition(format):
    """get the file formats for the metadata distribution blocks

    Notes:
        
    Args:
        format (str): file format
        
    Returns:
        (str): format description
    
    Raises:
    """
    return _FORMATS[format] if format in _FORMATS else 'Unknown'

def ogr_to_postgis(ogrgeom):
    pass


def ogr_to_kml_fieldtype(ogr_type):
    """get the kml field type from the ogr field type

    Notes:
        
    Args:
        ogr_type (OGR.FIELDTYPE): ogr field type
        
    Returns:
        (str): kml field type
    
    Raises:
    """
    if ogr_type in [ogr.OFTInteger]:
        return 'int'
    elif ogr_type in [ogr.OFTReal]:
        return 'double'
    else:
        return 'string'
    pass


'''
basic utils
'''
def encode_as_ascii(s):
    """encode the strings as ascii for any xml-based output

    Notes:
        gstore is utf-8 and there are special characters in the data
        
    Args:
        s (str): string to encode
        
    Returns:
        (str): ascii-encoded string
    
    Raises:
    """
    return ('%s' % s).encode('ascii', 'xmlcharrefreplace')

#convert to python by ogr_type
#probably want to make sure it's not null and not nodata (as defined by the attribute)
#and convert to str before encoding in case it is nodata
def convert_by_ogrtype(value, ogr_type, fmt='', datefmt=''):
    """convert the data value to the expected data type

    Notes:
        Includes special handling by expected output type like
        escaping strings for the xml-based output, etc
        
    Args:
        value (str): the value to try to convert
        ogr_type (OGR.FIELD_TYPE): ogr field type enum
        fmt (str): expected output format
        datefmt (str, optional): string for the datetime format
        
    Returns:
        (obj): the converted value in the correct format, or, if error, as string
    
    Raises:
    """
    if not value:
        return ''
    if ogr_type == ogr.OFTInteger:
        try :
            return int(value)
        except:
            pass
    if ogr_type == ogr.OFTReal:
        try:
            return float(value)
        except:
            pass
    if ogr_type == ogr.OFTDateTime:
        if datefmt:
            try:
                return datetime.strptime(value, datefmt)
            except:
                pass
                
    #it's just a string or the conversion failed for reasons
    value = encode_as_ascii(value) if fmt in ['kml', 'gml', 'csv'] else value.encode('utf-8')
    
    #and do one last check for kml, gml & ampersands, etc
    value = escape(unescape(value)) if fmt in ['kml', 'gml'] else value
    
    #wrap the string in double-quotes if it's a csv 
    #TODO: change the csv handling to something else
    value = '"%s"' % value if fmt in ['csv'] and ',' in value else value
    return value

'''
transformations & reprojections
'''
def epsg_to_sr(epsg):
    """convert an epsg integer to a spatial reference

    Notes:
        
    Args:
        epsg (int): epsg code
        
    Returns:
        (osr.SpatialReference): spatial reference object for the code
    
    Raises:
    """
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(epsg)
    return sr

def string_to_bbox(box):
    """convert string to a bbox

    Notes:
        
    Args:
        box (str): extent as minx,miny,maxx,maxy
        
    Returns:
        (list): bbox as list of floats [minx, miny, maxx, maxy]
    
    Raises:
    """
    try:
        if isinstance(box, basestring):
            bbox = map(float, box.split(','))
        else:
            #try as a list of strings
            bbox = map(float, box)
    except:
        bbox = []
    return bbox

def bbox_to_wkt(bbox):
    """convert bbox (list of floats) to WKT polygon

    Notes:
        Does not include spatial reference info.
        
    Args:
        bbox (list): extent as minx,miny,maxx,maxy floats
        
    Returns:
        (str): WKT Polygon for the bbox
    
    Raises:
    """
    return """POLYGON((%(minx)s %(miny)s,%(minx)s %(maxy)s,%(maxx)s %(maxy)s,%(maxx)s %(miny)s,%(minx)s %(miny)s))""" % { 'minx': bbox[0], 'miny': bbox[1], 'maxx': bbox[2], 'maxy': bbox[3]}

def geom_to_wkt(geom, srid=''):
    """convert geometry object to WKT representation

    Notes:
        This is not the geom as hex-encoded WKB!

        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        geom (Geometry): an ogr geometry object
        srid (str, optional): the epsg code (as EPSG:####) to preprend to the WKT 
        
    Returns:
        (str): the WKT for the geometry
    
    Raises:
    """
    wkt = geom.ExportToWkt()
    wkt = 'SRID=%s;%s' % (srid, wkt) if srid else wkt
    return wkt

def check_wkb_size(wkb):
    """check the size of the WKB representation

    Notes:
        Related to mongoimport document size limitations where, during the initial 
        migration, the size limit was 4MB for the document. In some cases, we have
        WKB geometries that exceed that.

        This has changed with new versions, but the need to check hasn't.
        
    Args:
        wkb (str): WKB representation of a geometry
        
    Returns:
        (float): size of the wkb in MB
    
    Raises:
    """
    return len(wkb.encode('utf-8')) *  0.0000009536743

def wkt_to_geom(wkt, epsg):
    """convert wkt to a geometry

    Notes:
        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        wkt (str): wkt string
        epsg (int): epsg code of the wkt
        
    Returns:
        (Geometry): ogr geometry from the wkt and with the provided spatial ref
    
    Raises:
    """
    sr = epsg_to_sr(epsg)
    geom = ogr.CreateGeometryFromWkt(wkt, sr)

    return geom

def bbox_to_wkb(bbox, epsg):
    """convert bbox to a hex-encoded wkb

    Notes:
        There seems to be no architectural need for the hex-encoding and the process
        to populate the legacy database stripped out the srid from the WKT. It is
        unfortunate but that is a big patch in postgres that hasn't been dealt with.

        It is reasonably safe to assume that all WKB (and geoms) in postgres are EPSG:4326
        (WGS84) but that is, for obvious reasons, unverifiable. Here be dragons.

        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        bbox (list): extent as minx,miny,maxx,maxy floats
        epsg (int): epsg code to use
        
    Returns:
        (string): hex-encoded wkb string
    
    Raises:
    """
    wkt = bbox_to_wkt(bbox)
    sr = epsg_to_sr(epsg)
    geom = ogr.CreateGeometryFromWkt(wkt, sr)
    return geom.ExportToWkb().encode('hex')

def bbox_to_geom(bbox, epsg):
    """convert bbox to geometry

    Notes:
        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        bbox (list): extent as minx,miny,maxx,maxy floats
        epsg (int): epsg code to use
        
    Returns:
        (Geometry): geometry object for the bbox in the specified epsg.
    
    Raises:
    """
    wkt = bbox_to_wkt(bbox)
    sr = epsg_to_sr(epsg)
    return ogr.CreateGeometryFromWkt(wkt, sr)

def geom_to_bbox(geom):
    """convert geometry to a bbox

    Notes:
        Geometry should already be in the desired projection.
        
    Args:
        geom (Geometry): geometry object
        
    Returns:
        (list): extent as minx,miny,maxx,maxy floats
    
    Raises:
    """
    env = geom.GetEnvelope()
    return [env[0], env[2], env[1], env[3]]
    
def geom_to_wkb(geom):
    """convert geometry to wkb

    Notes:
        
    Args:
        geom (Geometry): geometry object
        
    Returns:
        (str): hex-encoded wkb
    
    Raises:
    """
    return geom.ExportToWkb().encode('hex')

def wkb_to_bbox(wkb, epsg):
    """convert wkb to bbox

    Notes:
        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        wkb (str): hex-encoded wkb
        epsg (int): epsg code of the input wkb
        
    Returns:
        (list): extent as minx,miny,maxx,maxy floats
    
    Raises:
    """
    sr = epsg_to_sr(epsg)
    geom = ogr.CreateGeometryFromWkb(wkb.decode('hex'), sr)
    env = geom.GetEnvelope()
    return [env[0], env[2], env[1], env[3]]

def wkb_to_geom(wkb, epsg):
    """convert wkb to geometry

    Notes:
        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        wkb (str): hex-encoded wkb
        epsg (int): epsg code of the input wkb
        
    Returns:
        geom (Geometry): geometry object
    
    Raises:
    """
    sr = epsg_to_sr(epsg)
    return ogr.CreateGeometryFromWkb(wkb.decode('hex'), sr)

def reproject_geom(geom, in_epsg, out_epsg):
    """reproject a geometry

    Notes:
        Reprojects in place. Does not return a new geometry.
        
    Args:
        geom (Geometry): geometry object
        in_epsg (int): epsg code of the input geometry
        out_epsg (int): epsg code of the reprojected geometry
        
    Returns:
    
    Raises:
        
    """
    in_sr = epsg_to_sr(in_epsg)
    out_sr = epsg_to_sr(out_epsg)

    #make sure the geom has the in_sr
    geom.AssignSpatialReference(in_sr)

    try:
        geom.TransformTo(out_sr)
    except OGRError as err:
        return None

def wkb_to_output(wkb, epsg, output_type='kml'):
    """convert wkb to an output format

    Notes:
        The EPSG code is NOT for reprojection but for DEFINTION only.
        
    Args:
        wkb (str): hex-encoded wkb
        epsg (int): epsg code of the input wkb
        output_type (str, optional): format of the output object. Defaults to KML.
        
    Returns:
        (obj): the blob generated by the export (kml, gml, geojson)
    
    Raises:
    """
    geom = wkb_to_geom(wkb, epsg)
    
    if output_type == 'kml':
        return geom.ExportToKML()
    elif output_type == 'gml':
        return geom.ExportToGML()
    elif output_type == 'geojson':
        return geom.ExportToJson()
    else:
        return ''

'''
extent methods
'''

def check_for_valid_extent(bbox):
    """check for valid extents

    Notes:
        Extents provided by ogr for points have zero area
        and are not valid for MapServer.
        
    Args:
        bbox (list): extent as minx,miny,maxx,maxy floats
        
    Returns:
        (bool): true if the extent has area, false if not
    
    Raises:
    """
    return 0.0 < ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))

def buffer_point_extent(bbox, radius):
    """generate a valid extent (area > zero) for point geometries

    Notes:
        Extents provided by ogr for points have zero area
        and are not valid for MapServer.
        
    Args:
        bbox (list): extent as minx,miny,maxx,maxy floats in WGS84
        radius (float): buffer radius
        
    Returns:
        (list): extent as minx,miny,maxx,maxy floats
    
    Raises:
    """
    point = ogr.CreateGeometryFromWkt('POINT (%s %s)' % (bbox[0], bbox[1]))
    buf = point.Buffer(radius, 30)
    env = buf.GetEnvelope()
    return env[0], env[2], env[1], env[3]


