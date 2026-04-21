import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use /tmp for Vercel serverless, local path for development
DB_DIR = os.environ.get("DB_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.environ.get("VERCEL"):
    DB_DIR = "/tmp"

DB_PATH = os.path.join(DB_DIR, "cricket_scorer.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from api.models import (
        Tournament, Team, Player, Match,
        Innings, BallEvent, BattingScore, BowlingScore
    )
    Base.metadata.create_all(bind=engine)
