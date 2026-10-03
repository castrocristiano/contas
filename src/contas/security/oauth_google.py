import urllib.parse
from dataclasses import dataclass


@dataclass
class GoogleUserInfo:
    google_id: str
    email: str
    name: str
    avatar_url: str | None = None


class GoogleOAuthService:
    """Helper for Google OAuth 2.0 Web flow."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(
        self, client_id: str = "", client_secret: str = "", redirect_uri: str = ""
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def get_authorization_url(self, state: str = "contas_oauth") -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_user_info(self, code: str) -> GoogleUserInfo:
        """Exchanges an authorization code for user info from Google."""
        import requests

        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        token_resp = requests.post(self.TOKEN_URL, data=token_data, timeout=10)
        token_resp.raise_for_status()
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise ValueError("Falha ao obter access_token do Google.")

        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_resp = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
        userinfo_resp.raise_for_status()
        info = userinfo_resp.json()

        return GoogleUserInfo(
            google_id=info["sub"],
            email=info["email"],
            name=info.get("name") or info["email"].split("@")[0],
            avatar_url=info.get("picture"),
        )
