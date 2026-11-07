import os
os.chdir('/app/backend/orders_api')

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

cfg = Config('alembic.ini')

# What does ScriptDirectory see?
script = ScriptDirectory.from_config(cfg)
print("ScriptDirectory heads:", script.get_heads())
print("Revisions in versions/:", [r.revision for r in script.walk_revisions()])

# What does the DB see?
# Try both with and without version_table
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        # Look at pg_tables for ALL alembic tables
        r = await conn.execute(text("SELECT schemaname, tablename FROM pg_tables WHERE tablename LIKE '%alembic%'"))
        print("All alembic tables in DB:", r.fetchall())
        
        # Check each one's content
        for schema, table in r.fetchall():
            try:
                q = f'SELECT * FROM "{schema}"."{table}"'
                r2 = await conn.execute(text(q))
                rows = r2.fetchall()
                print(f"  {schema}.{table}: {rows}")
            except Exception as e:
                print(f"  {schema}.{table}: ERROR {e}")
    await engine.dispose()

asyncio.run(main())
