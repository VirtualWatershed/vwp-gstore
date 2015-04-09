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
        Column('model_run_id', UUID, FetchedValue()),
        Column('description', String(500)),
        Column('researcher_name', String(100)),
        Column('userid', String(100)),
        Column('model_run_name', String(300)),
        Column('model_keywords', String(500)),
        Column('start_date', TIMESTAMP, FetchedValue()),
        Column('end_date', TIMESTAMP, FetchedValue()),
        Column('id', Integer, primary_key=True),
        schema = 'gstoredata'
    )

    def __init__(self, model_run_id, description, researcher_name,userid,model_run_name,model_keywords):
        self.model_run_id, = model_run_id,
        self.description = description,
        self.researcher_name=researcher_name,
        self.userid=userid,
        self.model_run_name=model_run_name,
        self.model_keywords=model_keywords,

