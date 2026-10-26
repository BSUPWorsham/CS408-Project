#!/usr/bin/env python3
"""Tiny migration runner for the SQLite database.

Applies migrations/*.sql in filename order and records each one in a
schema_migrations table, so every script runs exactly once.

    python3 manage_db.py upgrade            # apply pending migrations
    python3 manage_db.py status             # show applied / pending
    python3 manage_db.py upgrade --db PATH  # use another database file

To add a change: create migrations/003_describe_change.sql, then run upgrade.
"""
import argparse
import glob
import os
import sqlite3
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")
DEFAULT_DB = os.path.join(BASE_DIR, "app", "instance", "aplin.db")


def migration_files():
    return sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))


def _connect(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY,"
        " applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    return conn


def applied_versions(conn):
    return {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}


def upgrade(db_path=DEFAULT_DB):
    """Apply pending migrations. Returns the list of versions applied."""
    conn = _connect(db_path)
    done = applied_versions(conn)
    applied = []
    try:
        for path in migration_files():
            version = os.path.basename(path)
            if version in done:
                continue
            with open(path, encoding="utf-8") as f:
                script = f.read()
            try:
                conn.executescript(
                    "BEGIN;\n" + script +
                    f"\nINSERT INTO schema_migrations (version) VALUES ('{version}');\nCOMMIT;"
                )
            except sqlite3.Error:
                if conn.in_transaction:
                    conn.rollback()
                raise
            applied.append(version)
    finally:
        conn.close()
    return applied


def status(db_path=DEFAULT_DB):
    conn = _connect(db_path)
    try:
        done = applied_versions(conn)
    finally:
        conn.close()
    return [(os.path.basename(p), os.path.basename(p) in done) for p in migration_files()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["upgrade", "status"])
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the SQLite file")
    args = parser.parse_args(argv)

    if args.command == "upgrade":
        applied = upgrade(args.db)
        if applied:
            for v in applied:
                print(f"applied  {v}")
        else:
            print("Database is up to date.")
    else:
        for version, is_done in status(args.db):
            print(f"{'applied' if is_done else 'pending':8} {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
