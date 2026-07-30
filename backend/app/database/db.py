"""Database engine and session management.

Auto-detects PostgreSQL vs SQLite. Falls back to SQLite when Docker/Postgres
is unavailable, so the app works with zero infrastructure dependencies.
"""

import asyncio
import os
import logging
import socket
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Smart URL resolution ──────────────────────────────────────
def _resolve_db_url() -> str:
    """Pick the best database URL:
    1. settings.DATABASE_URL (from .env) if set and Postgres is reachable
    2. SQLite fallback in data/
    """
    configured_url = settings.DATABASE_URL

    if configured_url:
        # Try connecting to Postgres
        if "postgres" in configured_url:
            try:
                host = "localhost"
                if "@" in configured_url:
                    host = configured_url.split("@")[1].split(":")[0]
                sock = socket.create_connection((host, 5432), timeout=2)
                sock.close()
                logger.info(f"Database: Using PostgreSQL — {configured_url}")
                return configured_url
            except (OSError, socket.error):
                logger.info(f"Database: PostgreSQL at '{configured_url}' unreachable, falling back to SQLite")
        else:
            # Non-Postgres URL (direct SQLite path, etc.)
            if configured_url.startswith("sqlite"):
                # SQLite path may need the full path resolved
                if configured_url.startswith("sqlite:///./"):
                    rel_path = configured_url[len("sqlite:///./"):]
                    abs_path = os.path.abspath(rel_path)
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    resolved = f"sqlite:///{abs_path}"
                    logger.info(f"Database: Using SQLite — {resolved}")
                    return resolved
            logger.info(f"Database: Using configured URL — {configured_url}")
            return configured_url

    # Fallback: SQLite in project data/ directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "infichat.db")
    sqlite_url = f"sqlite:///{db_path}"
    logger.info(f"Database: No DATABASE_URL configured, using SQLite — {sqlite_url}")
    return sqlite_url


_effective_url = _resolve_db_url()

# ── Engine ────────────────────────────────────────────────────
_connect_args = {}
if "sqlite" in _effective_url:
    _connect_args["check_same_thread"] = False

engine = create_engine(_effective_url, connect_args=_connect_args)

# ── Enable WAL mode + foreign keys for SQLite ─────────────────
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in _effective_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations() -> None:
    """Run ``alembic upgrade head`` programmatically against the live engine.

    Invoked at startup in production so a fresh database is built from
    migrations and existing ones pick up new revisions. Under multiple workers
    the first to acquire the migration lock applies changes; the rest see head
    and no-op, which Alembic handles safely.
    """
    from alembic import command
    from alembic.config import Config

    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg = Config(os.path.join(backend_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_root, "alembic"))
    # env.py resolves the URL itself via _resolve_db_url(), keeping this in sync
    # with the engine the app actually uses.
    command.upgrade(cfg, "head")
    logger.info("Database migrations applied (alembic upgrade head).")


async def init_db():
    """Bring the database schema up to date.

    Production: migrations are authoritative. We run ``alembic upgrade head``
    so the schema is built and evolved deterministically. create_all is NOT
    used in production because it silently ignores drift on existing tables —
    it never ALTERs, so a new column (e.g. consent tracking) would simply be
    missing and fail at runtime.

    Development / SQLite fallback: keep create_all plus the lightweight ad-hoc
    column adds for zero-friction local iteration.
    """
    from app.models.memory import Memory
    from app.models.file import File
    from app.models.chat import ChatSession, ChatMessage, SharedChat
    from app.models.otp import OTP
    from app.models.snippets import Snippet
    from app.models.user import User
    from app.models.admin import AdminProfile

    loop = asyncio.get_running_loop()

    if settings.is_production:
        await loop.run_in_executor(None, _run_migrations)
        return

    await loop.run_in_executor(None, Base.metadata.create_all, engine)

    # Auto-migration (safe for both Postgres and SQLite)
    def _migrate_schema():
        try:
            with engine.connect() as conn:
                from sqlalchemy import text as sa_text
                from app.core.compat import IS_SQLITE, migration_sqlite_safe

                # Build migration statements based on dialect
                migrations = [
                    ("users", "totp_secret", "VARCHAR"),
                    ("users", "is_mfa_enabled", "BOOLEAN DEFAULT FALSE"),
                    ("chat_messages", "model", "VARCHAR"),
                ]

                for table, column, col_type in migrations:
                    try:
                        if IS_SQLITE:
                            stmt = migration_sqlite_safe(table, column, col_type)
                        else:
                            stmt = f"ALTER TABLE {table} ADD COLUMN {col_type}"
                        conn.execute(sa_text(stmt))
                        conn.commit()
                        logger.info(f"Migration: added {table}.{column}")
                    except Exception:
                        conn.rollback()

                # PostgreSQL-specific migrations (skipped on SQLite)
                if not IS_SQLITE:
                    try:
                        conn.execute(sa_text(
                            "ALTER TABLE users ADD COLUMN organization_id UUID "
                            "REFERENCES organizations(id) ON DELETE SET NULL;"
                        ))
                        conn.commit()
                    except Exception:
                        conn.rollback()

        except Exception as e:
            logger.warning(f"Schema migration error (non-fatal): {e}")

    await loop.run_in_executor(None, _migrate_schema)


async def check_db_connection():
    """Test the database connection."""
    try:
        from sqlalchemy import text as sa_text
        loop = asyncio.get_running_loop()
        def _check():
            with engine.connect() as conn:
                conn.execute(sa_text("SELECT 1"))
        await loop.run_in_executor(None, _check)
        return True
    except Exception as e:
        logger.error(f"DATABASE CONNECTION FAILED: {e}")
        return False
