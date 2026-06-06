from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------
# DATABASE URL (modify password if you used something else)
# ---------------------------------------------------------
DATABASE_URL = "postgresql+psycopg2://postgres:Aggu%4012@localhost:5432/trading_terminal"

# ---------------------------------------------------------
# SQLAlchemy Engine
# ---------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=False,          # Set to True for SQL debugging
    future=True
)

# ---------------------------------------------------------
# Session Local
# ---------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# ---------------------------------------------------------
# Base class for models
# ---------------------------------------------------------
Base = declarative_base()

# ---------------------------------------------------------
# Dependency for FastAPI routes
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# Initialize DB (called on startup)
# ---------------------------------------------------------
def init_db():
    from app.db import models  # Import all models so SQLAlchemy sees them
    Base.metadata.create_all(bind=engine)
