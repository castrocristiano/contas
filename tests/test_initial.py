"""Initial baseline tests for the Contas project."""

from contas import main


def test_project_initialization() -> None:
    """Verify that project core package can be imported and executed."""
    assert callable(main)
