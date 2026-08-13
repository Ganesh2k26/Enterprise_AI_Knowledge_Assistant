from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.core.token_blacklist import is_refresh_token_revoked, revoke_refresh_token
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, TokenPair
from app.schemas.user import UserCreate, UserRead


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)

    @staticmethod
    def issue_tokens(user: User) -> TokenPair:
        subject = str(user.id)
        access_token = create_access_token(subject)
        refresh_token, _jti = create_refresh_token(subject)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def issue_auth_response(user: User) -> AuthResponse:
        tokens = AuthService.issue_tokens(user)
        return AuthResponse(user=UserRead.model_validate(user), **tokens.model_dump())

    async def register(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise ConflictError("An account with this email already exists.")

        unmet = validate_password_strength(payload.password)
        if unmet:
            raise ValidationAppError(f"Password must contain {', '.join(unmet)}.")

        org = Organization(name=payload.organization_name)
        self.db.add(org)
        await self.db.flush()

        hashed_password = hash_password(payload.password)
        user = User(
            email=payload.email,
            hashed_password=hashed_password,
            full_name=payload.full_name,
            role=UserRole.OWNER,
            organization_id=org.id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def register_and_authenticate(self, payload: UserCreate) -> AuthResponse:
        user = await self.register(payload)
        return self.issue_auth_response(user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")
        return user

    async def login(self, email: str, password: str) -> AuthResponse:
        user = await self.authenticate(email, password)
        return self.issue_auth_response(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """
        Refresh tokens rotate on every use: the presented token is
        immediately blacklisted (by jti) so it cannot be replayed, and a
        brand-new access/refresh pair is issued. This limits the blast
        radius of a leaked refresh token to a single use.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid or expired refresh token.")

        jti = payload.get("jti")
        if jti and await is_refresh_token_revoked(jti):
            raise UnauthorizedError("This refresh token has already been used. Please sign in again.")

        user = await self.users.get(payload["sub"])
        if not user:
            raise UnauthorizedError("User no longer exists.")

        if jti:
            remaining = int(payload["exp"] - datetime.now(timezone.utc).timestamp())
            await revoke_refresh_token(jti, remaining)

        return self.issue_tokens(user)
