# pylint: disable=redefined-outer-name
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
# pylint: disable=import-outside-toplevel
import pytest
from pytest import fixture
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase


@fixture()
def db_engine():
    """Create a test SQLAlchemy database engine."""
    engine = create_engine('sqlite:///:memory:')
    # engine = create_engine('sqlite:///ciao.test')
    return engine

@fixture
def sync_session_maker(db_engine):
    return sessionmaker(bind=db_engine)

@fixture()
def session(db_engine):
    """Create a SQLAlchemy database session."""
    return sessionmaker(bind=db_engine)()


@fixture()
def Base():
    """Create a SQLAlchemy Base model class."""
    class Base(DeclarativeBase):
        """Base model class for tesing purposes."""

    return Base

@fixture()
def user(Base, sync_session_maker, sync_context):
    """Create the basic user model."""
    from jsalchemy_authentication.mixins import IdentityMixin
    from jsalchemy_web_context.sync import db

    class User(IdentityMixin, Base):
        """Redefined User class."""
        __tablename__ = 'user'
        first_name = Column(String)
        last_name = Column(String)

    Base.metadata.create_all(bind=sync_session_maker().bind)

    with sync_context():
        db.add(User(first_name = 'John', last_name='Doe', unid = 'john doe', password='foo'))

    return User

@fixture
def sync_context(sync_session_maker):
    """Creates a context to be user withing an async with bloc."""
    from jsalchemy_web_context.sync.manager import ContextManager
    from fakeredis import FakeRedis

    return ContextManager(sync_session_maker, FakeRedis.from_url('redis://localhost:6379/0'))
