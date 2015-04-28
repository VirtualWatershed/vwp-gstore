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

from groups import Groups

class Users(Base):

    __table__ = Table('users', Base.metadata,
        Column('userid', String(100)),
        Column('firstname', String(100)),
        Column('lastname', String(100)),
        Column('email', String(100)),
        Column('salt', String(50)),
        Column('password', String(150)),
	Column('address1', String(150)),
        Column('address2', String(150)),
        Column('state', String(50)),
        Column('zipcode', String(15)),
        Column('tel_voice', String(20)),
        Column('tel_fax', String(20)),
	Column('city', String(100)),
        Column('country', String(100)),
        Column('id', Integer, primary_key=True),
        schema = 'gstoredata'
    )

    def __init__(self, userid, firstname, lastname, email, address1,address2, city, state, zipcode, tel_voice, tel_fax, country,salt, password):
        self.userid = userid,
        self.firstname = firstname,
        self.lastname=lastname,
        self.email=email,
        self.salt=salt,
	self.password=password,
	self.address1=address1,
	self.address2=address2,
	self.state=state,
	self.city=city,
	self.zipcode=zipcode,
	self.tel_voice=tel_voice,
	self.tel_fax=tel_fax,
	self.country=country,

    groups = relationship('Groups',
                    secondary='gstoredata.users_groups',
                    backref='users')

