import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read database URL from environment, fall back to local docker-compose default
DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql://postgres:postgres@localhost:5433/knowledgemate",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
