import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
elif DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    except Exception:
        engine = create_engine("sqlite:///savo_sitescout.db")
else:
    engine = create_engine("sqlite:///savo_sitescout.db")

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session