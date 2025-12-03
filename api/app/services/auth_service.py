from app.models.user import User


class AuthService:

    @classmethod
    def register(cls, user: User):
        pass

    @classmethod
    def login(email: str, password: str, invite_token: str | None = None) -> User:
        pass
