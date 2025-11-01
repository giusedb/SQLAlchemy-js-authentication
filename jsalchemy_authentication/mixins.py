from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column, Session
import bcrypt

from jsalchemy_web_context.sync import session as sync_session, db as sync_db
from jsalchemy_web_context.sync import session, db


class IdentityMixin:
    """Define the basic Identification information model."""
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

