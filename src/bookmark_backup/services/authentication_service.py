from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from bookmark_backup.db.models import Role, SystemRole, User

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


class AuthenticationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def register_editor(self, email: str, password: str) -> User:
        """Register a new user with the Editor role."""
        if self.session.scalar(select(User).where(User.email == email)):
            raise ValueError(f"User with email {email} already exists.")

        editor_role = self.session.scalar(
            select(Role).where(Role.name == SystemRole.EDITOR)
        )

        user = User(
            email=email,
            password=hash_password(password),
        )
        if editor_role:
            user.roles.append(editor_role)

        self.session.add(user)
        self.session.commit()
        return user

    def login(self, email: str, password: str) -> User | None:
        """Verify credentials and return the user if valid."""
        user = self.session.scalar(select(User).where(User.email == email))
        if user and verify_password(password, user.password):
            return user
        return None

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """Update password with history check (cannot reuse current or previous)."""
        if not verify_password(current_password, user.password):
            raise ValueError("Incorrect current password.")

        if verify_password(new_password, user.password):
            raise ValueError("New password cannot be the same as the current password.")

        if verify_password(new_password, user.previous_password):
            raise ValueError("New password cannot be the same as the previous password.")

        user.previous_password = user.password
        user.password = hash_password(new_password)
        self.session.commit()