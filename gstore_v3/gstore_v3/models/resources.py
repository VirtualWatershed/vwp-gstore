from gstore_v3.models import Base, DBSession
from sqlalchemy import MetaData, Table, ForeignKey
from sqlalchemy import Column, String, Integer, Boolean, FetchedValue, TIMESTAMP, Numeric
from sqlalchemy.orm import relationship, backref, deferred
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.dialects.postgresql import UUID

class ResourceStates(Base):

    __table__ = Table('resources_states', Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50)),
        Column('initials', String(2)),
        schema = 'gstoredata'
    )

    def __init__(self, name, initials):
        self.name=name
        selt.initials=initials

class ResourceCountries(Base):

    __table__ = Table('resources_countries', Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('initials', String(2)),
        schema = 'gstoredata'
    )

    def __init__(self, name, initials):
        self.name=name
        selt.initials=initials 

class ResourceInstitutions(Base):

    __table__ = Table('resources_institutions', Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(100)),
        Column('initials', String(10)),
        schema = 'gstoredata'
    )

    def __init__(self, name, initials):
        self.name=name
        selt.initials=initials

