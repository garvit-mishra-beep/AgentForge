import logging
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg

from core.config import settings

logger = logging.getLogger(__name__)


class DatabasePool:
    _pool: asyncpg.Pool | None = None

    async def initialize(self, retries: int = 3) -> None:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                self._pool = await asyncpg.create_pool(
                    dsn=settings.database_url,
                    min_size=settings.database_pool_min,
                    max_size=settings.database_pool_max,
                    command_timeout=30,
                )
                logger.info(
                    "Database pool initialized (min=%d, max=%d, attempt=%d)",
                    settings.database_pool_min, settings.database_pool_max, attempt + 1,
                )
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    "Database connection failed (attempt %d/%d): %s",
                    attempt + 1, retries, e,
                )
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"Failed to connect to database after {retries} attempts") from last_error

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")
        return self._pool

    async def run_migrations(self) -> None:
        await self._ensure_migration_table()
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        if not migration_files:
            logger.warning("No migration files found in %s", migrations_dir)
            return

        async with self.pool.acquire() as conn:
            for mf in migration_files:
                already_run = await conn.fetchval(
                    "SELECT COUNT(*) FROM schema_migrations WHERE filename = $1",
                    mf.name,
                )
                if already_run:
                    logger.debug("Migration already applied: %s", mf.name)
                    continue

                sql = mf.read_text()
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES ($1)",
                        mf.name,
                    )
                logger.info("Migration applied: %s", mf.name)
        logger.info("All migrations applied successfully")

    async def _ensure_migration_table(self) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id          SERIAL PRIMARY KEY,
                    filename    VARCHAR(255) NOT NULL UNIQUE,
                    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

    @asynccontextmanager
    async def transaction(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> str:
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
