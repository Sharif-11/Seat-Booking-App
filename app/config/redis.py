import redis.asyncio as redis
from app.config.settings import settings

redis_client = None


async def init_redis():
    global redis_client

    redis_client = redis.Redis(
       host=settings.REDIS_HOST,
       port=settings.REDIS_PORT,
       decode_responses=True,
       username=settings.REDIS_USERNAME,
       password=settings.REDIS_PASSWORD,

    )
    check = await redis_client.ping()
    await redis_client.ping()
    print("Redis connected")


async def close_redis():
    global redis_client

    if redis_client:
        await redis_client.close()
        print("Redis closed")


def get_redis():
    return redis_client