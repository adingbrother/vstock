from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/quant.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    # Create data folder and all tables defined under Base
    os.makedirs("./data", exist_ok=True)
    # Import models to register metadata
    try:
        from quant_web.models import models as _models
    except Exception:
        # if import fails, skip
        _models = None
    Base.metadata.create_all(bind=engine)

