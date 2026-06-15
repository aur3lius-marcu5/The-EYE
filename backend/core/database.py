from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


_COLUMN_CHECKS: dict[str, list[tuple[str, str]]] = {
    "targets": [
        ("passive_only", "INTEGER DEFAULT 0"),
        ("auto_pipeline", "INTEGER DEFAULT 1"),
        ("max_depth", "INTEGER DEFAULT 2"),
    ],
}


async def _migrate_sqlite(conn):
    import sqlalchemy as sa
    for table, cols in _COLUMN_CHECKS.items():
        existing = {c["name"] for c in (await conn.execute(sa.text(f"PRAGMA table_info({table})"))).mappings().all()}
        for col_name, col_type in cols:
            if col_name not in existing:
                await conn.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                import logging
                logging.getLogger(__name__).info(f"Added missing column {table}.{col_name}")


async def create_tables():
    async with engine.begin() as conn:
        from backend.core.models import Target, Scan, OSINTResult, Report, AIAnalysis, Finding, PipelineRun
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_sqlite(conn)
