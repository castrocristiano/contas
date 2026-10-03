from uuid import UUID

from contas.application.ports.repositories import IUserRepository
from contas.domain.entities import User
from contas.domain.errors import (
    AccountPendingApprovalError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from contas.schemas.user import (
    AdminResetPasswordInput,
    ApproveUserInput,
    AuthenticateUserInput,
    ChangePasswordInput,
    GoogleAuthInput,
    RegisterUserInput,
)
from contas.security.password import hash_password, verify_password


class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: RegisterUserInput) -> dict:
        # Check uniqueness
        if await self.user_repo.get_by_email(payload.email):
            raise UserAlreadyExistsError("e-mail", payload.email)
        if await self.user_repo.get_by_username(payload.username):
            raise UserAlreadyExistsError("login", payload.username)

        # First user is automatically admin and approved
        user_count = await self.user_repo.count()
        is_first = user_count == 0

        user = User(
            name=payload.name.strip(),
            email=payload.email.lower().strip(),
            username=payload.username.lower().strip(),
            password_hash=hash_password(payload.password),
            auth_provider="local",
            is_active=True,
            is_approved=is_first,  # First user approved, subsequent must be approved by admin
            role="admin" if is_first else "user",
        )
        created = await self.user_repo.create(user)
        return {
            "id": str(created.id),
            "name": created.name,
            "email": created.email,
            "username": created.username,
            "role": created.role,
            "is_approved": created.is_approved,
        }


class AuthenticateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: AuthenticateUserInput) -> dict:
        ident = payload.identifier.strip()
        user = await self.user_repo.get_by_email(ident)
        if not user:
            user = await self.user_repo.get_by_username(ident)

        if not user or not user.password_hash:
            raise InvalidCredentialsError()

        if not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        if not user.is_approved:
            raise AccountPendingApprovalError()

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "is_approved": user.is_approved,
        }


class GoogleOAuthUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: GoogleAuthInput) -> dict:
        # Check by google_id first
        user = await self.user_repo.get_by_google_id(payload.google_id)
        if not user:
            # Check by email
            user = await self.user_repo.get_by_email(payload.email)
            if user:
                # Link google_id and update avatar
                user.google_id = payload.google_id
                if payload.avatar_url:
                    user.avatar_url = payload.avatar_url
                await self.user_repo.update(user)
            else:
                # New user via Google
                user_count = await self.user_repo.count()
                is_first = user_count == 0
                new_username = payload.email.split("@")[0]
                # Ensure username uniqueness
                base_username = new_username
                suffix = 1
                while await self.user_repo.get_by_username(new_username):
                    new_username = f"{base_username}{suffix}"
                    suffix += 1

                user = User(
                    name=payload.name,
                    email=payload.email.lower().strip(),
                    username=new_username,
                    auth_provider="google",
                    google_id=payload.google_id,
                    avatar_url=payload.avatar_url,
                    is_active=True,
                    is_approved=is_first,
                    role="admin" if is_first else "user",
                )
                user = await self.user_repo.create(user)

        if not user.is_active:
            raise InvalidCredentialsError()

        if not user.is_approved:
            raise AccountPendingApprovalError()

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "is_approved": user.is_approved,
        }


class ApproveUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: ApproveUserInput) -> dict:
        user_uuid = UUID(payload.user_id)
        user = await self.user_repo.get_by_id(user_uuid)
        if not user:
            raise UserNotFoundError(payload.user_id)

        user.is_approved = payload.approve
        updated = await self.user_repo.update(user)
        return {
            "id": str(updated.id),
            "name": updated.name,
            "email": updated.email,
            "is_approved": updated.is_approved,
        }


class ListUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self) -> list[dict]:
        users = await self.user_repo.list_all()
        return [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "username": u.username,
                "auth_provider": u.auth_provider,
                "is_active": u.is_active,
                "is_approved": u.is_approved,
                "role": u.role,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]


class ChangePasswordUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: ChangePasswordInput) -> dict:
        user_uuid = UUID(payload.user_id)
        user = await self.user_repo.get_by_id(user_uuid)
        if not user:
            raise UserNotFoundError(payload.user_id)

        # If user already has a password, verify the current password
        if user.password_hash and not verify_password(
            payload.current_password, user.password_hash
        ):
            raise InvalidCurrentPasswordError()

        if len(payload.new_password) < 6:
            raise ValueError("A nova senha deve ter no mínimo 6 caracteres.")

        user.password_hash = hash_password(payload.new_password)
        await self.user_repo.update(user)
        return {
            "id": str(user.id),
            "message": "Senha atualizada com sucesso.",
        }


class AdminResetPasswordUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, payload: AdminResetPasswordInput) -> dict:
        user_uuid = UUID(payload.target_user_id)
        user = await self.user_repo.get_by_id(user_uuid)
        if not user:
            raise UserNotFoundError(payload.target_user_id)

        if len(payload.new_password) < 6:
            raise ValueError("A nova senha deve ter no mínimo 6 caracteres.")

        user.password_hash = hash_password(payload.new_password)
        await self.user_repo.update(user)
        return {
            "id": str(user.id),
            "message": f"Senha de {user.username} redefinida com sucesso pelo administrador.",
        }
