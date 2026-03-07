"""Create database and all tables"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import engine, Base
from backend.models import (  # noqa: F401 — import to register models
    User,
    TherapySession,
    SessionMessage,
    Assessment,
    TherapyTask,
    ProgressMetric,
    KnowledgeDocument,
)


async def create_tables():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Done! Tables created:")
    for table in Base.metadata.tables:
        print(f"  - {table}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
