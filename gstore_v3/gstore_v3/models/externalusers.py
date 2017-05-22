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


class Externalusers(Base):

    __table__ = Table('externalusers', Base.metadata,
        Column('uuid', UUID, primary_key=True),
        Column('appid', Integer),
        schema = 'gstoredata'
    )

    def __init__(self, uuid, appid):
        self.uuid = uuid,
        self.appid = appid,

#    groups = relationship('Groups', secondary='gstoredata.users_groups', backref='users')

