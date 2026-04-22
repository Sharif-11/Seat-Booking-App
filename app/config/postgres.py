import asyncpg

DB_POOL = None


async def init_db():
    global DB_POOL

    DB_POOL = await asyncpg.create_pool(
        user="postgres",
        password="123456",
        database="seat_booking",
        host="localhost",
        port=5432,
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