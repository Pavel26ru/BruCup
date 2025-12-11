import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Get database credentials from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 3306)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Check if essential database variables are set
if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError("Database credentials (DB_USER, DB_PASSWORD, DB_NAME) must be set in .env file.")

# Construct the database URL for SQLAlchemy
# Using mysql+mysqlconnector driver
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Create an async engine
# `echo=True` is useful for debugging to see the generated SQL
engine = create_async_engine(DATABASE_URL, echo=False)

# Create a configured "Session" class
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncSession:
    """Dependency provider for getting a database session."""
    async with async_session_maker() as session:
        yield session
