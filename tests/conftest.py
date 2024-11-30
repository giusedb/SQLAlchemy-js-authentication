from pytest import fixture
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, DeclarativeBase



@fixture()
def db_engine():
    engine = create_engine('sqlite:///:memory:')
    # engine = create_engine('sqlite:///ciao.test')
    return engine


@fixture()
def session(db_engine):
    return sessionmaker(bind=db_engine)()


@fixture()
def Base():
    class Base(DeclarativeBase):
        pass

    return Base

@fixture()
def user(Base, session):
    from quasar_authentication.mixins import IdentityMixin

    class User(IdentityMixin, Base):
        __tablename__ = 'user'
        first_name = Column(String)
        last_name = Column(String)

    Base.metadata.create_all(bind=session.bind)

    user = User(first_name = 'John', last_name='Doe', unid = 'john doe')
    user.set_password('foo')

    session.add(user)
    session.commit()
    return User

