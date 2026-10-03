"""Pytest configuration and test isolation fixtures."""

import logging

import psycopg
import pytest

from contas.config import settings

logger = logging.getLogger(__name__)


def _clean_database() -> None:
    """Truncate all application data tables using direct psycopg connection."""
    raw_url = settings.database_url
    clean_url = raw_url.replace("postgresql+psycopg://", "postgresql://")

    try:
        with (
            psycopg.connect(clean_url, autocommit=True, connect_timeout=3) as conn,
            conn.cursor() as cur,
        ):
            cur.execute(
                "TRUNCATE TABLE transaction, budget, category, account CASCADE;"
            )
    except (psycopg.OperationalError, psycopg.Error) as exc:
        logger.debug(
            "Database cleanup skipped (database offline or unreachable): %s", exc
        )


@pytest.fixture(autouse=True)
def clean_database_before_and_after(request: pytest.FixtureRequest):
    """Clean database tables before and after integration or DB tests."""
    test_path = str(request.fspath)
    is_integration = "integration" in test_path
    is_ui_services = "test_ui_services.py" in test_path

    if is_integration or is_ui_services:
        _clean_database()
        yield
        _clean_database()
    else:
        yield
