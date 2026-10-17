import base64
import json
import urllib.parse
from dataclasses import dataclass, field


@dataclass
class KeycloakUserInfo:
    sub: str
    email: str
    username: str
    name: str
    roles: list[str] = field(default_factory=list)
    avatar_url: str | None = None


def _decode_jwt_payload(token: str) -> dict:
    """Safely decodes the payload section of a JWT without external crypto deps."""
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


DEFAULT_OIDC_SCOPE = "openid email profile"


def _collect_string_roles(items: object) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {role for role in items if isinstance(role, str)}


def _extract_roles(claims: dict, client_id: str) -> list[str]:
    roles: set[str] = set()
    realm_access = claims.get("realm_access")
    if isinstance(realm_access, dict):
        roles.update(_collect_string_roles(realm_access.get("roles")))

    resource_access = claims.get("resource_access")
    if isinstance(resource_access, dict):
        client_res = resource_access.get(client_id)
        if isinstance(client_res, dict):
            roles.update(_collect_string_roles(client_res.get("roles")))

    roles.update(_collect_string_roles(claims.get("roles")))
    return sorted(roles)


class KeycloakOAuthService:
    """Helper for Keycloak OpenID Connect (OIDC) Web & Direct Grant flows."""

    def __init__(
        self,
        server_url: str = "",
        realm: str = "contas",
        client_id: str = "contas-app",
        client_secret: str = "",
        redirect_uri: str = "",
        internal_url: str = "",
    ):
        self.server_url = server_url.rstrip("/")
        self.internal_url = (internal_url or server_url).rstrip("/")
        self.realm = realm.strip()
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.redirect_uri = redirect_uri.strip()

    @property
    def is_configured(self) -> bool:
        return bool(
            self.server_url and self.realm and self.client_id and self.redirect_uri
        )

    @property
    def _public_oidc_base(self) -> str:
        return f"{self.server_url}/realms/{self.realm}/protocol/openid-connect"

    @property
    def _internal_oidc_base(self) -> str:
        return f"{self.internal_url}/realms/{self.realm}/protocol/openid-connect"

    def get_authorization_url(self, state: str = "contas_keycloak") -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": DEFAULT_OIDC_SCOPE,
            "state": state,
        }
        return f"{self._public_oidc_base}/auth?{urllib.parse.urlencode(params)}"

    def get_registration_url(self, state: str = "contas_keycloak") -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": DEFAULT_OIDC_SCOPE,
            "state": state,
        }
        return (
            f"{self._public_oidc_base}/registrations?{urllib.parse.urlencode(params)}"
        )

    def get_logout_url(self, post_logout_redirect_uri: str | None = None) -> str:
        target_uri = post_logout_redirect_uri or self.redirect_uri
        params = {
            "client_id": self.client_id,
            "post_logout_redirect_uri": target_uri,
        }
        return f"{self._public_oidc_base}/logout?{urllib.parse.urlencode(params)}"

    def _build_user_info(self, access_token: str) -> KeycloakUserInfo:
        import requests

        jwt_claims = _decode_jwt_payload(access_token)
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_resp = requests.get(
            f"{self._internal_oidc_base}/userinfo", headers=headers, timeout=10
        )
        userinfo_resp.raise_for_status()
        info = userinfo_resp.json()

        merged = {**jwt_claims, **info}
        sub = str(merged.get("sub") or "")
        if not sub:
            raise ValueError("Resposta do Keycloak não contém identificador 'sub'.")

        username = str(
            merged.get("preferred_username")
            or merged.get("username")
            or merged.get("email", "").split("@")[0]
            or sub
        )
        email = str(merged.get("email") or f"{username}@keycloak.local")
        name = str(merged.get("name") or merged.get("given_name") or username)
        roles = _extract_roles(merged, self.client_id)

        return KeycloakUserInfo(
            sub=sub,
            email=email,
            username=username,
            name=name,
            roles=roles,
            avatar_url=merged.get("picture"),
        )

    def exchange_code_for_user_info(self, code: str) -> KeycloakUserInfo:
        """Exchanges an OIDC authorization code for user info from Keycloak."""
        import requests

        token_data = {
            "client_id": self.client_id,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        if self.client_secret:
            token_data["client_secret"] = self.client_secret

        token_resp = requests.post(
            f"{self._internal_oidc_base}/token", data=token_data, timeout=10
        )
        token_resp.raise_for_status()
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise ValueError("Falha ao obter access_token do Keycloak.")

        return self._build_user_info(access_token)

    def authenticate_with_password(
        self, username: str, password: str
    ) -> KeycloakUserInfo:
        """Authenticates user via Keycloak Direct Access Grant (Resource Owner Password Credentials)."""
        import requests

        token_data = {
            "client_id": self.client_id,
            "username": username,
            "password": password,
            "grant_type": "password",
            "scope": DEFAULT_OIDC_SCOPE,
        }
        if self.client_secret:
            token_data["client_secret"] = self.client_secret

        token_resp = requests.post(
            f"{self._internal_oidc_base}/token", data=token_data, timeout=10
        )
        token_resp.raise_for_status()
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise ValueError("Falha ao obter access_token do Keycloak.")

        return self._build_user_info(access_token)
