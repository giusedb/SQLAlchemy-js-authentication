# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
# pylint: disable=too-few-public-methods

from sqlalchemy import Column, String, Integer, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.util import hybridproperty

from jsalchemy_authentication.mixins import IdentityMixin
from jsalchemy_web_context.sync import db, session

def test_extention(Base, sync_session_maker, sync_context):
    """Test the extensibility of User class"""

    class User(IdentityMixin, Base):
        __tablename__ = 'user'
        first_name = Column(String)
        last_name = Column(String)

    Base.metadata.create_all(bind=sync_session_maker().bind)

    with sync_context():
        user = User(first_name = 'John', last_name='Doe', unid = 'john doe', password='foo')
        db.add(user)

    with sync_context():
        fetch_user = db.execute(select(User).where(User.unid == 'john doe')).scalar_one()

        assert fetch_user is not None, 'User not saved'
        assert fetch_user.first_name == 'John', 'Missing name'
        assert fetch_user.last_name == 'Doe', 'Missing last name'

        assert fetch_user.check_password('foo') is True, 'Password incorrect'
        assert fetch_user.check_password('bar') is False, 'Anyone can login with the wrong password'

def test_login(user, sync_context):
    """Test the login capability."""

    with sync_context():
        identity = user.login('john doe', 'foo')
        assert identity is not None, 'Login failed'

        assert identity.first_name == 'John', 'Missing name'
        assert identity.last_name == 'Doe', 'Missing last name'

        assert user.login('john doe', 'bar') is None, 'Anyone can login with the wrong password'
        assert user.login('john do', 'foo') is None, 'login with wrong username'

def test_rename(Base, sync_session_maker, sync_context):
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

    Base.metadata.create_all(bind=sync_session_maker().bind)

    with sync_context():
        db.add(User(username='foo', email='foo@bar.com', password='foobar'))

    with sync_context():

        l_user = User.login('foo', 'foobar')
        assert l_user.email == 'foo@bar.com', 'Login failed'
        assert l_user.username == 'foo', 'Login failed'

def test_mutation(Base, sync_session_maker, sync_context):
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

    Base.metadata.create_all(bind=sync_session_maker().bind)

    with sync_context():
        db.add(User(username='foo', email='foo@bar.com', password='foobar'))

    with sync_context():
        l_user = db.execute(select(User).where(User.email == 'foo@bar.com')).scalar_one()
        assert l_user is not None, 'User saved'
        assert repr(l_user) == "User('foo', 'foo@bar.com')"

def test_foreign_keys(Base, user, sync_session_maker, sync_context):
    """Test relations among parents and children objects."""

    class Child(Base):
        __tablename__ = 'child'
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str]
        parent_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=True)

        parent: Mapped[user] = relationship(user, backref='children')

        def __str__(self):
            return f'Child({self.id, self.parent})'

    Base.metadata.create_all(bind=sync_session_maker().bind)

    with sync_context():
        o_user = user(unid='foo', first_name='John', last_name='Doe', password='foobar')
        db.add(o_user)
        db.add(Child(name='a', parent=o_user))
        db.add(Child(name='b', parent=o_user))

    with sync_context():
        l_user = db.execute(select(user).where(user.unid == 'foo')).scalar_one()
        assert l_user is not None, 'User saved'
        assert len(l_user.children) == 2, 'Child saved'
        for child in l_user.children:
            assert child.parent == l_user, f"Child {child} is not associated with user {l_user}"

        child = db.execute(select(Child)).first()[0]
        assert child.parent == l_user, f"Child {child} is not associated with user {l_user}"

def test_login(user, sync_context):
    """Test the login capability."""

    token = None

    with sync_context() as ctx:
        l_user = user.login('john doe', 'foo')
        token = ctx.token

    with sync_context(token):
        d_user = db.execute(select(user).where(user.unid == 'john doe')).scalar_one()
        for k in ('first_name', 'last_name', 'unid'):
            assert session.user[k] == getattr(d_user, k)
