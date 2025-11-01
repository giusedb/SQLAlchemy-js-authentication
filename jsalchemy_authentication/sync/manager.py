from types import FunctionType

import bcrypt
from sqlalchemy import select, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from jsalchemy_auth.sync.models import UserMixin
from ..mixins import IdentityMixin
from jsalchemy_web_context import ContextManager, db

class AuthenticationManager:

    def __init__(self, identity_model: IdentityMixin, context: ContextManager,
                 salt: str, user_prop: str='user', identified_by: str = 'username',
                 password_field: str = 'password'):
        if password_field not in identity_model.__mapper__.attrs:
            raise ValueError(f'Password field {password_field} not found in user model')
        if identified_by not in identity_model.__mapper__.attrs:
            raise ValueError(f'Identified by field {identified_by} not found in user model')
        if user_prop not in identity_model.__mapper__.attrs:
            raise ValueError(f'User prop {user_prop} not found in user model')
        self.identity_model = identity_model
        self.password_field = password_field
        self.context = context
        self.salt = salt.encode('ascii')
        self.field_set = {f.key for f in identity_model.__mapper__.attrs}
        self.unid = getattr(identity_model, identified_by)
        self.user_prop = user_prop

    def login(self, username, password) -> DeclarativeBase | None:
        query = (select(self.identity_model)
                 .where(self.unid == username))
        with self.context() as ctx:
            result = db.execute(query)
            identity = result.scalar_one_or_none()
            if not identity:
                return None
            if not bcrypt.checkpw(password.encode('utf-8'), identity.password.encode('ascii')):
                return None
            return getattr(identity.awaitable_attrs, self.user_prop)

    def register(self, user: dict) -> IdentityMixin:
        with self.context():
            db_user = {k: v for k, v in user.items() if k in self.field_set}
            user_obj = self.identity_model(**db_user)
            db.add(user_obj)
            db.commit()
            user['id'] = user_obj.id
            return user

    def user_exists(self, unid: str) -> bool:
        query = select(self.identity_model).where(self.unid == unid)
        with self.context() as session:
            user = db.execute(query).scalar_one_or_none()
        if user:
            return True
        return False
