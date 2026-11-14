from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from contas.security.session import (
    create_session_token,
    verify_session_token,
)


def test_create_and_verify_session_token_success():
    uid = uuid4()
    secret = "test-secret-key-12345-very-long-secret-key-for-hmac-sha256"
    token = create_session_token(uid, expires_in_days=1, secret_key=secret)
    assert isinstance(token, str)
    assert len(token) > 20

    verified_id = verify_session_token(token, secret_key=secret)
    assert verified_id == uid


def test_verify_session_token_expired():
    uid = uuid4()
    secret = "test-secret-key-12345-very-long-secret-key-for-hmac-sha256"
    now = datetime.now(UTC)
    expired_payload = {
        "sub": str(uid),
        "iat": int((now - timedelta(days=2)).timestamp()),
        "exp": int((now - timedelta(days=1)).timestamp()),
    }
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

    verified_id = verify_session_token(expired_token, secret_key=secret)
    assert verified_id is None


def test_verify_session_token_invalid_signature():
    uid = uuid4()
    secret_one = "test-secret-key-12345-very-long-secret-key-for-hmac-sha256-one"
    secret_two = "test-secret-key-12345-very-long-secret-key-for-hmac-sha256-two"
    token = create_session_token(uid, expires_in_days=1, secret_key=secret_one)
    verified_id = verify_session_token(token, secret_key=secret_two)
    assert verified_id is None


def test_verify_session_token_malformed():
    assert verify_session_token("not-a-valid-token") is None
    assert verify_session_token("") is None


def test_verify_session_token_missing_sub():
    secret = "test-secret-key-12345-very-long-secret-key-for-hmac-sha256"
    token = jwt.encode({"hello": "world"}, secret, algorithm="HS256")
    assert verify_session_token(token, secret_key=secret) is None
