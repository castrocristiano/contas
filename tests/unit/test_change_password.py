import pytest

from contas.application.use_cases.auth import (
    AdminResetPasswordUseCase,
    ChangePasswordUseCase,
    RegisterUserUseCase,
)
from contas.domain.entities import User
from contas.domain.errors import InvalidCurrentPasswordError
from contas.schemas.user import (
    AdminResetPasswordInput,
    ChangePasswordInput,
    RegisterUserInput,
)
from contas.security.password import verify_password


class InMemoryUserRepository:
    def __init__(self):
        self.users: dict = {}

    async def get_by_id(self, user_id):
        return self.users.get(user_id)

    async def get_by_email(self, email):
        for u in self.users.values():
            if u.email == email.lower():
                return u
        return None

    async def get_by_username(self, username):
        for u in self.users.values():
            if u.username == username.lower():
                return u
        return None

    async def get_by_google_id(self, google_id):
        for u in self.users.values():
            if u.google_id == google_id:
                return u
        return None

    async def count(self):
        return len(self.users)

    async def list_all(self, limit=100, offset=0):
        return list(self.users.values())[offset : offset + limit]

    async def create(self, user: User):
        self.users[user.id] = user
        return user

    async def update(self, user: User):
        self.users[user.id] = user
        return user


@pytest.mark.anyio
async def test_change_password_success_and_verify():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)
    change_uc = ChangePasswordUseCase(repo)

    created = await reg_uc.execute(
        RegisterUserInput(
            name="Alice Silva",
            email="alice@test.com",
            username="alice",
            password="oldPassword123",
        )
    )
    user_id = created["id"]

    # 1. Change password with correct current password
    res = await change_uc.execute(
        ChangePasswordInput(
            user_id=user_id,
            current_password="oldPassword123",
            new_password="newSecretPassword456",
        )
    )
    assert res["id"] == user_id

    # Verify updated hash
    user = await repo.get_by_email("alice@test.com")
    assert verify_password("newSecretPassword456", user.password_hash)
    assert not verify_password("oldPassword123", user.password_hash)


@pytest.mark.anyio
async def test_change_password_wrong_current_password_raises_error():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)
    change_uc = ChangePasswordUseCase(repo)

    created = await reg_uc.execute(
        RegisterUserInput(
            name="Bob Souza",
            email="bob@test.com",
            username="bob",
            password="correctPassword123",
        )
    )

    with pytest.raises(InvalidCurrentPasswordError):
        await change_uc.execute(
            ChangePasswordInput(
                user_id=created["id"],
                current_password="wrongPassword",
                new_password="someNewPassword123",
            )
        )


@pytest.mark.anyio
async def test_admin_reset_password():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)
    admin_reset_uc = AdminResetPasswordUseCase(repo)

    created = await reg_uc.execute(
        RegisterUserInput(
            name="Carlos User",
            email="carlos@test.com",
            username="carlos",
            password="initialPassword",
        )
    )
    user_id = created["id"]

    res = await admin_reset_uc.execute(
        AdminResetPasswordInput(
            target_user_id=user_id,
            new_password="provisionalPassword123",
        )
    )
    assert res["id"] == user_id

    user = await repo.get_by_email("carlos@test.com")
    assert verify_password("provisionalPassword123", user.password_hash)
