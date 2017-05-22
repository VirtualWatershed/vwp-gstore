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


class ExternalApps(Base):

    __table__ = Table('externalapplications', Base.metadata,
        Column('name', String(100)),
        Column('userid', Integer),
        Column('appid', Integer, primary_key=True),
        schema = 'gstoredata'
    )

    def __init__(self, name, userid):
        self.name = name,
        self.userid = userid,

