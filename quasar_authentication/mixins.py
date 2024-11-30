from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, Session
import bcrypt

class IdentityMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unid: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    def set_password(self, password: str) -> None:
        """Encrypt and store the password."""
        salt = bcrypt.gensalt(5)
        self.password = bcrypt.hashpw(password.encode('utf-8'), salt)

    def check_password(self, password: str) -> bool:
        """verify the password against the stored password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def __repr__(self):
        return f"Identity({self.unid})"

    def __str__(self):
        return self.unid

    @classmethod
    def login(cls, session: Session, unid: str, password: str) -> "IdentityMixin":
        """Find the user with the given unid and verify their password."""
        identity = session.query(cls).filter_by(unid=unid).first()
        if identity and identity.check_password(password):
            return identity

