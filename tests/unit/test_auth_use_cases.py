import pytest

from contas.application.ports.repositories import IUserRepository
from contas.application.use_cases.auth import (
    ApproveUserUseCase,
    AuthenticateUserUseCase,
    RegisterUserUseCase,
)
from contas.domain.entities import User
from contas.domain.errors import (
    AccountPendingApprovalError,
    UserAlreadyExistsError,
)
from contas.schemas.user import (
    ApproveUserInput,
    AuthenticateUserInput,
    RegisterUserInput,
)


class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self.users: dict = {}

    async def get_by_id(self, user_id):
        return self.users.get(user_id)

    async def get_by_email(self, email: str):
        for u in self.users.values():
            if u.email == email.lower().strip():
                return u
        return None

    async def get_by_username(self, username: str):
        for u in self.users.values():
            if u.username == username.lower().strip():
                return u
        return None

    async def get_by_google_id(self, google_id: str):
        for u in self.users.values():
            if u.google_id == google_id:
                return u
        return None

    async def count(self) -> int:
        return len(self.users)

    async def list_all(self, limit: int = 100, offset: int = 0):
        return list(self.users.values())[offset : offset + limit]

    async def create(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def update(self, user: User) -> User:
        self.users[user.id] = user
        return user


@pytest.mark.anyio
async def test_first_user_is_admin_and_approved():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)
    auth_uc = AuthenticateUserUseCase(repo)

    res = await reg_uc.execute(
        RegisterUserInput(
            name="Super Admin",
            email="admin@example.com",
            username="admin",
            password="securepassword123",
        )
    )
    assert res["role"] == "admin"
    assert res["is_approved"] is True

    # Can authenticate immediately
    logged = await auth_uc.execute(
        AuthenticateUserInput(
            identifier="admin",
            password="securepassword123",
        )
    )
    assert logged["username"] == "admin"
    assert logged["role"] == "admin"


@pytest.mark.anyio
async def test_second_user_is_not_approved_until_admin_approves():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)
    auth_uc = AuthenticateUserUseCase(repo)
    approve_uc = ApproveUserUseCase(repo)

    # 1. Admin registered
    await reg_uc.execute(
        RegisterUserInput(
            name="Admin",
            email="admin@example.com",
            username="admin",
            password="adminpassword",
        )
    )

    # 2. Second user registers
    user2 = await reg_uc.execute(
        RegisterUserInput(
            name="Cliente Normal",
            email="cliente@example.com",
            username="cliente",
            password="clientepassword",
        )
    )
    assert user2["role"] == "user"
    assert user2["is_approved"] is False

    # 3. User tries to log in and receives AccountPendingApprovalError
    with pytest.raises(AccountPendingApprovalError):
        await auth_uc.execute(
            AuthenticateUserInput(
                identifier="cliente",
                password="clientepassword",
            )
        )

    # 4. Admin approves user
    approved = await approve_uc.execute(
        ApproveUserInput(
            user_id=user2["id"],
            approve=True,
        )
    )
    assert approved["is_approved"] is True

    # 5. User can now authenticate
    logged = await auth_uc.execute(
        AuthenticateUserInput(
            identifier="cliente",
            password="clientepassword",
        )
    )
    assert logged["username"] == "cliente"


@pytest.mark.anyio
async def test_duplicate_email_or_username_raises_error():
    repo = InMemoryUserRepository()
    reg_uc = RegisterUserUseCase(repo)

    await reg_uc.execute(
        RegisterUserInput(
            name="User 1",
            email="user1@example.com",
            username="user1",
            password="password123",
        )
    )

    with pytest.raises(UserAlreadyExistsError, match="e-mail"):
        await reg_uc.execute(
            RegisterUserInput(
                name="User 2",
                email="user1@example.com",
                username="user2",
                password="password123",
            )
        )

    with pytest.raises(UserAlreadyExistsError, match="login"):
        await reg_uc.execute(
            RegisterUserInput(
                name="User 3",
                email="user3@example.com",
                username="user1",
                password="password123",
            )
        )
