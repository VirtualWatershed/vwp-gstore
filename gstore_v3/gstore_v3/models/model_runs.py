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

class Modelruns(Base):
    
    __table__ = Table('model_runs', Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('model_run_id', UUID, FetchedValue()),
        Column('description', String(500)),
        Column('start_date', TIMESTAMP, FetchedValue()),
        Column('end_date', TIMESTAMP, FetchedValue()),
        schema = 'gstoredata'
    )

    def __init__(self, model_run_id, description):
        self.model_run_id, = model_run_id,
        self.description = description,
