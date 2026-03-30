import aiosqlite
from contextlib import asynccontextmanager
from app.config import settings

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    return _db


async def open_db():
    global _db
    _db = await aiosqlite.connect(settings.db_path)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA foreign_keys=ON")
    await _db.commit()


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
