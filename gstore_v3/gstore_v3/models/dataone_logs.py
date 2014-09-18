from gstore_v3.models import DataoneBase, DataoneSession
from sqlalchemy import MetaData, Table, ForeignKey
from sqlalchemy import Column, String, Integer, Boolean, FetchedValue, TIMESTAMP, Numeric
from sqlalchemy.orm import relationship, backref

from sqlalchemy import desc, asc, func

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

from sqlalchemy.dialects.postgresql import UUID, ARRAY

import os

'''
This is a separate postgres database just for the dataone logging. 
It is tied to a different session, etc. FYI.
'''

class DataoneLog(DataoneBase):
    """dateone log table

    You have to flag the READs to the dataone API with a method
    that is not GET or POST but READ. Not going to modify apache logs 
    for that so here you go.

    Note:
        it's in its own special database because we need
        write access for the logging and the errors and we're not
        enabling that for the main datastore.

    Attributes:
        
    """
    __table__ = Table('logs', DataoneBase.metadata,
        Column('id', Integer, primary_key=True),
        Column('identifier', String(500)),
        Column('ip_address', String(20)),
        Column('useragent', String(50)),
        Column('subject', String(200)),
        Column('logged', TIMESTAMP, FetchedValue()), 
        Column('event', String(20)),
        Column('node', String(100))
    )

    def __init__(self, identifier, ip_address, subject, event, node, useragent='public'):
        """add a new record

        Notes:
            
        Args:
            identifier (string): object identifer
            ip_address (string): ip address of the client
            subject (string): 
            event (string): read or replica
            node (string):
            useragent (string): 
                    
        Returns:
        
        Raises:
        """
        self.identifier = identifier
        self.ip_address = ip_address
        self.useragent = useragent
        self.subject = subject
        self.event = event
        self.node = node

    def __repr__(self):
        return '<Log (%s, %s, %s, %s)>' % (self.id, self.identifier, self. event, self.logged)

    #TODO: maybe just go back to the template? meh. six of one, probably.
    def get_log_entry(self):
        """return a logEntry xml element

        Example (the template):
            <logEntry>
                <entryId>${d['id']}</entryId>
                <identifier>${d['identifier']}</identifier>
                <ipAddress>${d['ip']}</ipAddress>
                <userAgent>${d['useragent']}</userAgent>
                <subject>${d['subject']}</subject>
                <event>${d['event']}</event>
                <dateLogged>${d['dateLogged']}</dateLogged>
                <nodeIdentifier>${d['node']}</nodeIdentifier>
            </logEntry>

        Notes:
            
        Args:
                    
        Returns:
        
        Raises:
        """
        fmt = '%Y-%m-%dT%H:%M:%S+00:00'
        entry = """<logEntry>
                    <entryId>%(id)s</entryId>
                    <identifier>%(identifier)s</identifier>
                    <ipAddress>%(ip)s</ipAddress>
                    <userAgent>%(useragent)s</userAgent>
                    <subject>%(subject)s</subject>
                    <event>%(event)s</event>
                    <dateLogged>%(logged)s</dateLogged>
                    <nodeIdentifier>%(node)s</nodeIdentifier>
                   </logEntry>""" % {'id':self.id, 'identifier':self.identifier, 'ip':self.ip_address, 'useragent':self.useragent, 'subject':self.subject, 'event':self.event, 'logged':self.logged.strftime(fmt), 'node':self.node}
        return entry

    def get_json(self):
        """return a logEntry json blob if you want to return to the template

        Notes:
            
        Args:
                    
        Returns:
        
        Raises:
        """
        fmt = '%Y-%m-%dT%H:%M:%S+00:00'
        return {'id': self.id, 'identifier': self.identifier, 'ip': self.ip_address, 'useragent': self.useragent, 'subject': self.subject, 'event': self.event, 'dateLogged': self.logged.strftime(fmt), 'node': self.node}

    #TODO: deal with session and user agent (not as string)
    #      we have little to no info about the session other than it's 
    #      a "normal" one. do not make that assumption about d1.


class DataoneError(DataoneBase):
    """dateone error table

    For the error POSTs

    Note:
        there is nothing in tier one about returning these to anyone.

    Attributes:
        
    """
    __table__ = Table('errors', DataoneBase.metadata,
        Column('id', Integer, primary_key=True),
        Column('message', String(500)),
        Column('received', TIMESTAMP, FetchedValue())
    )

    def __init__(self, message):
        """add an error entry

        Notes:
            
        Args:
            message (str): the error message (which is an xml blob) as text in postgres
                    
        Returns:
        
        Raises:
        """
        self.message = message
        
    def __repr__(self):
        return '<DataONE Error: %s, %s>' % (self.id, self.received)
    
    
