import os
import aiosqlite
from app.config import settings


async def init_schema(db: aiosqlite.Connection):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        schema = f.read()
    await db.executescript(schema)
    await db.commit()
