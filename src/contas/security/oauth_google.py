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
