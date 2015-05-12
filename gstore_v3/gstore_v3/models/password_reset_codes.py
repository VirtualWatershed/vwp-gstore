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

class Password_Reset_Codes(Base):

    __table__ = Table('password_reset_codes', Base.metadata,
        Column('userid', String(100)),
        Column('resetcode', String(130)),
        Column('id', Integer, primary_key=True),
        schema = 'gstoredata'
    )

    def __init__(self, userid, resetcode):
        self.userid = userid,
        self.resetcode = resetcode,

