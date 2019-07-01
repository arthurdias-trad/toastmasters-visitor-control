# encoding: utf-8
# encoding: iso-8859-1
# encoding: win-1252

import csv
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug import generate_password_hash
from os import getenv


URL = getenv("DATABASE_URL")

engine = create_engine(URL)
db = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(length=50))
    password = Column(String(length=255))

    def __repr__(self):
        return f"Username={self.username}, password={self.password}"

class Member(Base):
    __tablename__ = 'members'

    member_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    id_type = Column(String(20), nullable=False)
    id_number = Column(String(30), nullable=False)

class Guest(Base):
    __tablename__ = 'guests'

    guest_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(255), nullable=False)
    id_type = Column(String(20), nullable=False)
    id_number = Column(String(30), nullable=False)
    tm_member = Column(Boolean, nullable=False)


Base.metadata.create_all(engine)
