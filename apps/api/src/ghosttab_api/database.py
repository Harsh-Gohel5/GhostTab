from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def make_engine(url: str):
    if url.startswith("sqlite"):
        Path(".ghosttab").mkdir(exist_ok=True)
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 20}
        if url.startswith("sqlite")
        else {},
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_settings(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return engine


def sessions(engine):
    return sessionmaker(engine, expire_on_commit=False)
