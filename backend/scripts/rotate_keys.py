"""Re-encrypt data at rest under a new E2E_ENCRYPTION_KEY.

Why this exists
---------------
The previous E2E/RAG encryption keys shipped as literal defaults in
``app/core/config.py`` and are therefore in git history — permanently public.
Rotating the key is what makes the leaked value worthless, but a naive rotation
silently orphans every existing encrypted row: ``EncryptedText`` swallows
decryption errors and returns raw ciphertext, so the damage surfaces later as
garbled chat history rather than a crash.

This script decrypts with the OLD key and re-encrypts with the NEW one.

Encrypted columns (all raw Fernet via ``app/models/utils.py``):
  - chat_messages.content        (EncryptedText)
  - memories.content            (EncryptedText)
  - shared_chats.snapshot_json  (EncryptedJSON)

``RAG_ENCRYPTION_KEY`` needs no migration: ``rag_service.py`` treats the leaked
default as "no key" and stored those documents as plaintext. Setting a real key
encrypts documents indexed from then on.

Usage
-----
Always dry-run first, and take a database backup before ``--apply``::

    # 1. See what would change (no writes)
    python -m scripts.rotate_keys --old-key "<current>" --new-key "<new>"

    # 2. Apply for real
    python -m scripts.rotate_keys --old-key "<current>" --new-key "<new>" --apply

Generate a new key with::

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Afterwards set ``E2E_ENCRYPTION_KEY`` in ``backend/.env`` to the new value and
restart. Rows already using the new key are detected and skipped, so an
interrupted run is safe to resume.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("rotate_keys")


@dataclass(frozen=True)
class EncryptedColumn:
    """A single column holding Fernet ciphertext."""

    table: str
    pk: str
    column: str


# Mirrors the EncryptedText/EncryptedJSON columns in app/models/.
ENCRYPTED_COLUMNS: tuple[EncryptedColumn, ...] = (
    EncryptedColumn("chat_messages", "id", "content"),
    EncryptedColumn("memories", "id", "content"),
    EncryptedColumn("shared_chats", "id", "snapshot_json"),
)


@dataclass
class ColumnStats:
    """Outcome tally for one column."""

    rotated: int = 0
    already_new: int = 0
    plaintext: int = 0
    undecryptable: int = 0

    @property
    def total(self) -> int:
        return self.rotated + self.already_new + self.plaintext + self.undecryptable


def _table_exists(conn, table: str) -> bool:
    """True when the table is present (schemas vary across deployments)."""
    from sqlalchemy import inspect

    return table in inspect(conn).get_table_names()


def rotate_column(
    conn,
    col: EncryptedColumn,
    old: Fernet,
    new: Fernet,
    *,
    apply: bool,
) -> ColumnStats:
    """Re-encrypt one column, classifying every row.

    Rows are only rewritten when they decrypt cleanly under the old key. A row
    that already uses the new key, holds legacy plaintext, or decrypts under
    neither is left untouched — rewriting those would destroy data.
    """
    stats = ColumnStats()
    if not _table_exists(conn, col.table):
        logger.info("  %s.%s — table absent, skipping", col.table, col.column)
        return stats

    rows = conn.execute(
        text(f"SELECT {col.pk} AS pk, {col.column} AS val FROM {col.table}")  # noqa: S608
    ).fetchall()

    for row in rows:
        value = row.val
        if value is None or value == "":
            continue
        raw = value.encode() if isinstance(value, str) else value

        # Already rotated? Then the new key opens it.
        try:
            new.decrypt(raw)
            stats.already_new += 1
            continue
        except InvalidToken:
            pass

        try:
            plaintext = old.decrypt(raw)
        except InvalidToken:
            # Not ciphertext under either key: legacy plaintext written before
            # encryption existed, or corrupt. Leave it alone.
            if str(value).startswith("gAAAAA"):
                stats.undecryptable += 1
                logger.warning(
                    "  %s.%s pk=%s — Fernet token decrypts under neither key; left as-is",
                    col.table,
                    col.column,
                    row.pk,
                )
            else:
                stats.plaintext += 1
            continue

        if apply:
            conn.execute(
                text(
                    f"UPDATE {col.table} SET {col.column} = :val WHERE {col.pk} = :pk"  # noqa: S608
                ),
                {"val": new.encrypt(plaintext).decode(), "pk": row.pk},
            )
        stats.rotated += 1

    return stats


def build_fernet(label: str, key: str) -> Fernet:
    """Construct a Fernet, failing with an actionable message."""
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:  # noqa: BLE001 - surfaced to the operator
        raise SystemExit(
            f"{label} is not a valid Fernet key ({exc}).\n"
            "Expected 32 url-safe base64-encoded bytes. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        ) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-encrypt data at rest under a new E2E_ENCRYPTION_KEY.",
    )
    parser.add_argument("--old-key", required=True, help="Current E2E_ENCRYPTION_KEY")
    parser.add_argument("--new-key", required=True, help="Replacement E2E_ENCRYPTION_KEY")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes. Omit for a dry run (default).",
    )
    args = parser.parse_args(argv)

    if args.old_key == args.new_key:
        raise SystemExit("--old-key and --new-key are identical; nothing to rotate.")

    old = build_fernet("--old-key", args.old_key)
    new = build_fernet("--new-key", args.new_key)

    # Imported here so --help works without a configured environment.
    from app.database.db import engine

    mode = "APPLY (writing)" if args.apply else "DRY RUN (no writes)"
    logger.info("Key rotation — %s", mode)
    logger.info("Database: %s", engine.url.render_as_string(hide_password=True))

    totals = ColumnStats()
    # One transaction: either every column rotates or none does.
    with engine.begin() as conn:
        for col in ENCRYPTED_COLUMNS:
            stats = rotate_column(conn, col, old, new, apply=args.apply)
            if stats.total:
                logger.info(
                    "  %s.%s — %d to rotate, %d already new, %d plaintext, %d undecryptable",
                    col.table,
                    col.column,
                    stats.rotated,
                    stats.already_new,
                    stats.plaintext,
                    stats.undecryptable,
                )
            totals.rotated += stats.rotated
            totals.already_new += stats.already_new
            totals.plaintext += stats.plaintext
            totals.undecryptable += stats.undecryptable

        if not args.apply:
            # Belt and braces: nothing should have been written anyway.
            conn.rollback()

    logger.info(
        "Summary: %d rotated, %d already on new key, %d plaintext, %d undecryptable",
        totals.rotated,
        totals.already_new,
        totals.plaintext,
        totals.undecryptable,
    )

    if totals.undecryptable:
        logger.warning(
            "%d row(s) look like Fernet tokens but opened under neither key. "
            "They were left untouched — investigate before discarding the old key.",
            totals.undecryptable,
        )

    if args.apply:
        logger.info("Done. Set E2E_ENCRYPTION_KEY to the new value and restart.")
    else:
        logger.info("Dry run only. Back up your database, then re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
