"""Alembic migration environment — auto-detects SQLite vs PostgreSQL."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add backend root to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Alembic Config
config = context.config

# Override SQLAlchemy URL with the app's resolved URL
from app.database.db import _resolve_db_url
config.set_main_option("sqlalchemy.url", _resolve_db_url())

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Base.metadata is complete
from app import models
from app.database.db import Base

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Render the project's portable column types with clean, importable code.

    Autogenerate's default repr for these TypeDecorators emits invalid Python
    (e.g. ``none_as_null=<class ...>``). We render them as their public names
    from app.models.types instead. ArrayType is checked before JSONType because
    it subclasses it.
    """
    if type_ == "type":
        from app.core.compat import PortableUUID, JSONType
        from app.models.types import ArrayType

        if isinstance(obj, ArrayType):
            autogen_context.imports.add("import app.models.types")
            return "app.models.types.ArrayType()"
        if isinstance(obj, JSONType):
            autogen_context.imports.add("import app.models.types")
            return "app.models.types.JSONB()"
        if isinstance(obj, PortableUUID):
            autogen_context.imports.add("import app.models.types")
            as_uuid = getattr(obj, "_as_uuid", True)
            return f"app.models.types.UUID(as_uuid={as_uuid})"
    # Fall back to Alembic's default rendering for everything else.
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
