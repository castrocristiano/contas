import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import streamlit.components.v1 as components

from contas.config import settings

logger = logging.getLogger(__name__)


def create_session_token(
    user_id: str | UUID,
    expires_in_days: int | None = None,
    secret_key: str | None = None,
) -> str:
    """Generates a signed JWT session token for the user."""
    effective_secret = secret_key or settings.secret_key
    days = (
        expires_in_days
        if expires_in_days is not None
        else settings.session_cookie_expire_days
    )
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=days)).timestamp()),
    }
    return jwt.encode(payload, effective_secret, algorithm="HS256")


def verify_session_token(
    token: str,
    secret_key: str | None = None,
) -> UUID | None:
    """Validates the JWT session token and returns the user UUID if valid."""
    effective_secret = secret_key or settings.secret_key
    try:
        payload = jwt.decode(token, effective_secret, algorithms=["HS256"])
        sub = payload.get("sub")
        if not sub:
            return None
        return UUID(str(sub))
    except (jwt.PyJWTError, ValueError) as exc:
        logger.debug("Invalid session token: %s", exc)
        return None


def render_set_cookie_script(
    token: str,
    cookie_name: str | None = None,
    days: int | None = None,
) -> None:
    """Injects JavaScript to set a persistent cookie and localStorage in the browser."""
    c_name = cookie_name or settings.session_cookie_name
    c_days = days if days is not None else settings.session_cookie_expire_days
    # Use max-age in seconds for modern browsers and expires for older ones
    max_age_seconds = c_days * 24 * 3600
    js = f"""
    <script>
    (function() {{
        var cookieName = "{c_name}";
        var token = "{token}";
        var days = {c_days};
        var maxAge = {max_age_seconds};
        var expires = "";
        if (days) {{
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = "; expires=" + date.toUTCString();
        }}
        var cookieStr = cookieName + "=" + encodeURIComponent(token) + expires + "; max-age=" + maxAge + "; path=/; SameSite=Lax";
        try {{
            window.parent.document.cookie = cookieStr;
        }} catch (e) {{}}
        try {{
            document.cookie = cookieStr;
        }} catch (e) {{}}
    }})();
    </script>
    """
    components.html(js, height=0, width=0)


def render_clear_cookie_script(
    cookie_name: str | None = None,
) -> None:
    """Injects JavaScript to delete the session cookie and localStorage."""
    c_name = cookie_name or settings.session_cookie_name
    js = f"""
    <script>
    (function() {{
        var cookieName = "{c_name}";
        var cookieStr = cookieName + "=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
        try {{
            window.parent.document.cookie = cookieStr;
        }} catch (e) {{}}
        try {{
            document.cookie = cookieStr;
        }} catch (e) {{}}
    }})();
    </script>
    """
    components.html(js, height=0, width=0)
