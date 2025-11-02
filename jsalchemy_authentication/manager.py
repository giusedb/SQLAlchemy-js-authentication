from types import FunctionType

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty

from jsalchemy_auth.sync.models import UserMixin
from jsalchemy_auth.utils import invert_prop
from .mixins import IdentityMixin
from jsalchemy_web_context import ContextManager, db

class AuthenticationManager:

    def __init__(self, identity_model: IdentityMixin, context: ContextManager,
                 salt: str, user_prop: str='user', identified_by: str = 'username',
                 password_field: str = 'password'):
        if password_field not in identity_model.__mapper__.attrs:
            raise ValueError(f'Password field {password_field} not found in user model')
        if identified_by not in identity_model.__mapper__.attrs:
            raise ValueError(f'Identifyed by field {identified_by} not found in user model')
        if user_prop not in identity_model.__mapper__.attrs:
            raise ValueError(f'User prop {user_prop} not found in user model')
        self.identity_model = identity_model
        self.password_field = password_field
        self.context = context
        self.salt = salt.encode('ascii')
        self.field_set = {f.key for f in identity_model.__mapper__.attrs}
        self.unid = getattr(identity_model, identified_by)
        self.user_prop = user_prop
        self.user_model = getattr(identity_model, user_prop).prop.entity.entity
        self.inv_user_prop = self._inv_prop(getattr(self.identity_model, user_prop).prop).key

    def _inv_prop(self, prop: RelationshipProperty):
        if prop.back_populates:
            return prop.entity.relationships[prop.back_populates]
        if isinstance(prop.backref, str):
            return prop.entity.relationships[prop.backref]

    async def login(self, username, password) -> DeclarativeBase | None:
        query = (select(self.identity_model)
                 .where(self.unid == username))
        async with self.context() as ctx:
            result = await db.execute(query)
            identity = result.scalar_one_or_none()
            if not identity:
                return None
            if not bcrypt.checkpw(password.encode('utf-8'), identity.password.encode('ascii')):
                return None
            return await getattr(identity.awaitable_attrs, self.user_prop)

    async def register(self, user: dict) -> IdentityMixin:
        async with self.context():
            db_user = {k: v for k, v in user.items() if k in self.field_set}
            user_mapper = self.user_model.__mapper__
            identity_obj = self.identity_model(**db_user)
            user_fields = {p.key for p in user_mapper.columns if p not in user_mapper.primary_key}
            user_obj = self.user_model(**{k: v for k, v in user.items() if k in user_fields})
            getattr(user_obj, self.inv_user_prop, identity_obj).append(identity_obj)
            db.add(identity_obj)
            db.add(user_obj)
            await db.flush()
            user['id'] = user_obj.id
            await db.commit()
            return user

    async def user_exists(self, unid: str) -> bool:
        query = select(self.identity_model).where(self.unid == unid)
        async with self.context() as session:
            user = (await db.execute(query)).scalar_one_or_none()
        if user:
            return True
        return False
