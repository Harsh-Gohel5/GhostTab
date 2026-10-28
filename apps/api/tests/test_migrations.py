"""Exercise upgrades against a disposable database, never the local workspace."""

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_worker_presence_upgrade_preserves_existing_task(tmp_path, monkeypatch):
    database = tmp_path / "upgrade.db"
    monkeypatch.setenv("GHOSTTAB_DATABASE_URL", f"sqlite:///{database.as_posix()}")
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "apps/api/migrations"))
    command.upgrade(config, "0001")
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO tasks (id,owner_id,title,goal,generation,created_at) VALUES (?,?,?,?,?,?)",
            ("synthetic-task", "test-owner", "Preserve this task", "Test upgrade", 1, 0),
        )
    command.upgrade(config, "head")
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT title FROM tasks").fetchone()[0] == "Preserve this task"
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0002"
        assert connection.execute("SELECT count(*) FROM worker_heartbeats").fetchone()[0] == 0
