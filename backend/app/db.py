import logging
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings


logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_pgvector_extension() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()
        logger.info("pgvector extension ensured.")
    except Exception as exc:
        logger.warning("Could not create pgvector extension: %s", exc)


def check_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    logger.info("Database connection OK.")

