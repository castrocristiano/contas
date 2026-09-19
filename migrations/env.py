"""Alembic environment configuration for async SQLModel migrations."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Import all models so SQLModel.metadata is fully populated before autogenerate.
# New models must be imported here to be detected by Alembic.
from contas.config import settings
from contas.models import Account, Budget, Category, Transaction  # noqa: F401

# Alembic Config object — provides access to the .ini file values.
config = context.config

# Override sqlalchemy.url from environment variable or settings.
database_url = os.getenv("DATABASE_URL") or settings.database_url
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata — source of truth for autogenerate.
target_metadata = SQLModel.metadata


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given synchronous connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect changes in Numeric precision and Enum values
        compare_server_default=True,  # Detect changes in column server defaults
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (psycopg3)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a live connection."""
    asyncio.run(run_async_migrations())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode with literal SQL output."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
