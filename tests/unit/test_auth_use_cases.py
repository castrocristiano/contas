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


@pytest.mark.anyio
async def test_keycloak_oauth_use_case_admin_and_regular_users():
    from contas.application.use_cases.auth import KeycloakOAuthUseCase
    from contas.schemas.user import KeycloakAuthInput

    repo = InMemoryUserRepository()
    kc_uc = KeycloakOAuthUseCase(repo)

    # 1. First user via Keycloak (becomes admin and approved)
    first_res = await kc_uc.execute(
        KeycloakAuthInput(
            keycloak_id="kc-sub-1",
            email="kc_admin@example.com",
            username="kc_admin",
            name="Keycloak Admin",
            roles=["user"],
        )
    )
    assert first_res["role"] == "admin"
    assert first_res["is_approved"] is True

    # 2. Second user via Keycloak with 'admin' role in Keycloak is also auto-approved
    second_res = await kc_uc.execute(
        KeycloakAuthInput(
            keycloak_id="kc-sub-2",
            email="kc_role_admin@example.com",
            username="kc_admin",  # colliding username should get suffix kc_admin1
            name="Role Admin",
            roles=["admin"],
        )
    )
    assert second_res["role"] == "admin"
    assert second_res["is_approved"] is True
    assert second_res["username"] == "kc_admin1"

    # 3. Third user without admin role requires approval
    pending_input = KeycloakAuthInput(
        keycloak_id="kc-sub-3",
        email="regular@example.com",
        username="regular_user",
        name="Regular User",
        roles=["user"],
    )
    with pytest.raises(AccountPendingApprovalError):
        await kc_uc.execute(pending_input)

    # 4. Existing user logging in again with 'admin' role gets promoted and approved
    promoted = await kc_uc.execute(
        KeycloakAuthInput(
            keycloak_id="kc-sub-3",
            email="regular@example.com",
            username="regular_user",
            name="Regular User Updated",
            roles=["admin"],
            avatar_url="https://example.com/avatar.png",
        )
    )
    assert promoted["is_approved"] is True
    assert promoted["role"] == "admin"
    assert promoted["name"] == "Regular User Updated"


def test_keycloak_oauth_service_urls_and_token_exchange(monkeypatch):
    import base64
    import json

    from contas.security.oauth_keycloak import KeycloakOAuthService

    svc = KeycloakOAuthService(
        server_url="http://localhost:8180",
        internal_url="http://keycloak:8080",
        realm="contas",
        client_id="contas-app",
        client_secret="test-client-secret",
        redirect_uri="http://localhost:8501",
    )
    assert svc.is_configured is True
    auth_url = svc.get_authorization_url()
    assert (
        "http://localhost:8180/realms/contas/protocol/openid-connect/auth" in auth_url
    )
    assert "client_id=contas-app" in auth_url

    reg_url = svc.get_registration_url()
    assert "/protocol/openid-connect/registrations" in reg_url

    logout_url = svc.get_logout_url()
    assert "/protocol/openid-connect/logout" in logout_url

    # Build a fake JWT with realm_access and resource_access roles
    header_b64 = (
        base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode())
        .decode()
        .rstrip("=")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "sub": "kc-uuid-999",
                    "preferred_username": "cristiano",
                    "realm_access": {"roles": ["admin", "user"]},
                    "resource_access": {"contas-app": {"roles": ["manager"]}},
                }
            ).encode()
        )
        .decode()
        .rstrip("=")
    )
    fake_jwt = f"{header_b64}.{payload_b64}.sig"

    class FakeResponse:
        def __init__(self, payload: dict):
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    def fake_post(url, data=None, timeout=10):
        assert url == "http://keycloak:8080/realms/contas/protocol/openid-connect/token"
        assert data["client_id"] == "contas-app"
        return FakeResponse({"access_token": fake_jwt})

    def fake_get(url, headers=None, timeout=10):
        assert (
            url == "http://keycloak:8080/realms/contas/protocol/openid-connect/userinfo"
        )
        assert headers["Authorization"] == f"Bearer {fake_jwt}"
        return FakeResponse(
            {
                "sub": "kc-uuid-999",
                "email": "cristiano@example.com",
                "name": "Cristiano Castro",
                "picture": "https://example.com/pic.png",
            }
        )

    import requests

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)

    info_code = svc.exchange_code_for_user_info("auth-code-123")
    assert info_code.sub == "kc-uuid-999"
    assert info_code.email == "cristiano@example.com"
    assert info_code.username == "cristiano"
    assert "admin" in info_code.roles
    assert "manager" in info_code.roles

    info_pwd = svc.authenticate_with_password("cristiano", "pass")
    assert info_pwd.sub == "kc-uuid-999"
    assert info_pwd.name == "Cristiano Castro"
