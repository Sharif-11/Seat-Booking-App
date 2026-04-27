# app/modules/redis/redis_connection.py
import redis.asyncio as redis
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

redis_client = None


async def init_redis():
    global redis_client

    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
            username=settings.REDIS_USERNAME,
            password=settings.REDIS_PASSWORD,
            socket_connect_timeout=5,  # Add timeout
            socket_timeout=5,
            retry_on_timeout=True,
        )

        await redis_client.ping()
        logger.info("Redis connected successfully")
        
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    except redis.TimeoutError as e:
        logger.error(f"Redis connection timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        raise


async def close_redis():
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
            logger.info("Redis closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


def get_redis():
    if redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return redis_client