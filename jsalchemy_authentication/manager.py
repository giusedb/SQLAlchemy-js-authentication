import time
from types import FunctionType

import bcrypt
from sqlalchemy import false, select

from jsalchemy_authorization.models import UserMixin


class AuthenticationManager:

    def __init__(self, user_model: UserMixin, session_maker: FunctionType, salt: bytes):
        self.user_model = user_model
        self.session_maker = session_maker
        self.salt = salt.encode('ascii')
        self.field_set = {f.key for f in user_model.__mapper__.attrs}

    async def login(self, username, password) -> dict | None:
        query = (select(self.user_model)
                 .where(self.user_model.username == username))
        async with self.session_maker() as session:
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                return None
            if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('ascii')):
                return None
            return user

    async def register(self, user: dict) -> UserMixin:
        async with self.session_maker() as session:
            db_user = {k: v for k, v in user.items() if k in self.field_set}
            user.password = str(bcrypt.hashpw(user.password.encode('utf-8'), self.salt), encoding='ascii')
            user_obj = self.user_model(**db_user)
            session.add(user_obj)
            await session.commit()
            return user_obj

    async def user_exists(self, username: str) -> bool:
        query = (select(self.user_model).where(self.user_model.username == username))
        async with self.session_maker() as session:
            user = (await session.execute(query)).scalar_one_or_none()
            if user:
                return True
            return False
