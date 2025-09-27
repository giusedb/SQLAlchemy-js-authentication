from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session
import bcrypt

from jsalchemy_web_context.sync import session as sync_session, db as sync_db
from jsalchemy_web_context.sync import session, db


class IdentityMixin:
    """Define the basic Identification information model."""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    def __init__(self, *args, **kwargs):
        password = kwargs.pop('password', None)
        super().__init__(**kwargs)
        if password:
            self.set_password(password)

    def set_password(self, password: str) -> None:
        """Encrypt and store the password."""
        salt = bcrypt.gensalt(5)
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """verify the password against the stored password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def __repr__(self):
        return f"Identity({self.unid})"

    def __str__(self):
        return self.unid

    @classmethod
    def login(cls, unid: str, password: str) -> "IdentityMixin":
        """Find the user with the given unid and verify their password."""
        identity = (
            sync_db.execute(
                select(cls)
                .where(cls.unid == unid)).scalar_one_or_none())
        if identity and identity.check_password(password):
            dct = identity.__dict__.copy()
            dct.pop('_sa_instance_state', None)
            sync_session.user = dct
            return identity
        return None

    @classmethod
    async def async_login(cls, unid: str, password: str) -> "IdentityMixin":
        identity = (await db.execute(select(cls).where(cls.unid == unid))).scalar_one_or_none()
        if identity and identity.check_password(password):
            dct = identity.__dict__.copy()
            dct.pop('_sa_instance_state', None)
            session.user = dct
            return identity
        return None

