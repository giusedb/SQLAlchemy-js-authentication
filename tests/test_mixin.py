# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods

from sqlalchemy import Column, String, Integer, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.util import hybridproperty

from jsalchemy_authentication.mixins import IdentityMixin
from jsalchemy_web_context.sync import db, session


def test_extention(Base, session):
    """Test the extensibility of User class"""

    class User(IdentityMixin, Base):
        __tablename__ = 'user'
        first_name = Column(String)
        last_name = Column(String)

    Base.metadata.create_all(bind=session.bind)

    user = User(first_name = 'John', last_name='Doe', unid = 'john doe')
    user.set_password('foo')

    session.add(user)
    session.commit()
    fetch_user = session.query(User).filter(User.unid == 'john doe').first()

    assert fetch_user is not None, 'User not saved'
    assert fetch_user.first_name == 'John', 'Missing name'
    assert fetch_user.last_name == 'Doe', 'Missing last name'

    assert fetch_user.check_password('foo') is True, 'Password incorrect'
    assert fetch_user.check_password('bar') is False, 'Anyone can login with the wrong password'


def test_login(user, session):
    """Test the login capability."""
    identity = user.login(session, 'john doe', 'foo')
    assert identity is not None, 'Login failed'

    assert identity.first_name == 'John', 'Missing name'
    assert identity.last_name == 'Doe', 'Missing last name'

    assert user.login(session, 'john doe', 'bar') is None, 'Anyone can login with the wrong password'
    assert user.login(session, 'john do', 'foo') is None, 'login with wrong username'


def test_rename(Base, session):
    """Test the rename of the `unid` column."""
    class User(IdentityMixin, Base):
        __tablename__ = 'user'
        email = Column(String)


        @hybridproperty
        def username(self):  # pylint: disable=missing-function-docstring
            return self.unid

        def __init__(self, **kwargs):
            username = kwargs.pop('username', None)
            if username:
                kwargs['unid'] = username
            super().__init__(**kwargs)

    Base.metadata.create_all(bind=session.bind)

    user = User(username='foo', email='foo@bar.com')
    user.set_password('foobar')

    session.add(user)
    session.commit()

    l_user = User.login(session, 'foo', 'foobar')
    assert l_user.email == 'foo@bar.com', 'Login failed'
    assert l_user.username == 'foo', 'Login failed'

def test_mutation(Base, session):
    """Test the mutation of the `IdentityMixin` class."""
    class User(IdentityMixin, Base):
        __tablename__ = 'user'
        email = Column(String)


        @hybridproperty
        def username(self):  # pylint: disable=missing-function-docstring
            return self.unid

        def __init__(self, **kwargs):
            username = kwargs.pop('username', None)
            if username:
                kwargs['unid'] = username
            super().__init__(**kwargs)

        def __repr__(self):
            return f"User('{self.username}', '{self.email}')"

    Base.metadata.create_all(bind=session.bind)

    user = User(username='foo', email='foo@bar.com')
    user.set_password('foobar')

    session.add(user)
    session.commit()

    l_user = session.query(User).filter(User.email == 'foo@bar.com').one()
    assert l_user is not None, 'User saved'
    assert repr(l_user) == "User('foo', 'foo@bar.com')"

def test_foreign_keys(Base, user, session):
    """Test relations among parents and children objects."""

    class Child(Base):
        __tablename__ = 'child'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str]
        parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=True)

        parent: Mapped[user] = relationship(user, backref='children')

        def __str__(self):
            return f'Child({self.id, self.parent})'

    Base.metadata.create_all(bind=session.bind)

    o_user = user(unid='foo', first_name='John', last_name='Doe')
    o_user.set_password('foobar')
    session.add(o_user)
    session.add(Child(name='a', parent=o_user))
    session.add(Child(name='b', parent=o_user))
    session.commit()

    l_user = session.query(user).filter(user.unid == 'foo').one()
    assert l_user is not None, 'User saved'
    assert len(l_user.children) == 2, 'Child saved'
    for child in l_user.children:
        assert child.parent == l_user, f"Child {child} is not associated with user {l_user}"

    child = session.query(Child).first()
    assert child.parent == l_user, f"Child {child} is not associated with user {l_user}"
