import sqlite3
import manage_db
from app import db

EXPECTED_TABLES = {"Users", "Intakes", "IntakeStatusHistory", "ContactSubmissions", "schema_migrations"}


def tables(path):
    conn = sqlite3.connect(path)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def test_upgrade_creates_all_tables(tmp_path):
    path = str(tmp_path / "t.db")
    applied = manage_db.upgrade(path)
    assert applied  # at least 001 and 002
    assert EXPECTED_TABLES <= tables(path)


def test_upgrade_is_idempotent(tmp_path):
    path = str(tmp_path / "t.db")
    manage_db.upgrade(path)
    assert manage_db.upgrade(path) == []
    assert all(done for _, done in manage_db.status(path))


def test_migrated_schema_matches_models(app, tmp_path):
    """Guards against editing models.py without adding a migration."""
    path = str(tmp_path / "t.db")
    manage_db.upgrade(path)
    conn = sqlite3.connect(path)
    try:
        for name, table in db.metadata.tables.items():
            cols = {r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')}
            assert cols == {c.name for c in table.columns}, f"{name} columns differ from migrations"
    finally:
        conn.close()
