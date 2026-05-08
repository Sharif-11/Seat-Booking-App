import asyncpg

from app.config.settings import settings

DB_POOL = None


async def init_db():
    global DB_POOL

    DB_POOL = await asyncpg.create_pool(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        min_size=1,
        max_size=10,
    )

    print("Postgres connected")


async def close_db():
    global DB_POOL

    if DB_POOL:
        await DB_POOL.close()
        print("Postgres closed")


def get_db():
    return DB_POOL