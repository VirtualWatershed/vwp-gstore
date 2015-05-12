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

users_groups = Table('users_groups', Base.metadata,
    Column('users_id', Integer, ForeignKey('gstoredata.users.id')),
    Column('groups_id', Integer, ForeignKey('gstoredata.groups.id')),
    Column('id', Integer, primary_key=True),
    schema='gstoredata'
)



class Groups(Base):

    __table__ = Table('groups', Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('groupname', String(100)),
        schema = 'gstoredata'
    )

    def __init__(self, groupname):
        self.groupname=groupname

