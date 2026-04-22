import redis.asyncio as redis

redis_client = None


async def init_redis():
    global redis_client

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    await redis_client.ping()
    print("Redis connected")


async def close_redis():
    global redis_client

    if redis_client:
        await redis_client.close()
        print("Redis closed")


def get_redis():
    return redis_client