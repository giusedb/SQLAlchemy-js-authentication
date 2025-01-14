# pylint: disable=redefined-outer-name
# pylint: disable=too-few-public-methods
# pylint: disable=invalid-name
# pylint: disable=import-outside-toplevel

from pytest import fixture
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase


@fixture()
def db_engine():
    """Create a test SQLAlchemy database engine."""
    engine = create_engine('sqlite:///:memory:')
    # engine = create_engine('sqlite:///ciao.test')
    return engine


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
def user(Base, session):
    """Create the basic user model."""
    from quasar_authentication.mixins import IdentityMixin

    class User(IdentityMixin, Base):
        """Redefined User class."""
        __tablename__ = 'user'
        first_name = Column(String)
        last_name = Column(String)

    Base.metadata.create_all(bind=session.bind)

    user = User(first_name = 'John', last_name='Doe', unid = 'john doe')
    user.set_password('foo')

    session.add(user)
    session.commit()
    return User
