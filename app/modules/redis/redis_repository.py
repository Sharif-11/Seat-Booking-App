# app/modules/redis/redis_repository.py
import logging
from typing import Optional, Any
import redis.asyncio as redis
from app.modules.redis.redis_connection import get_redis

logger = logging.getLogger(__name__)

class RedisOperationError(Exception):
    pass

class RedisRepository:
    def __init__(self):
        self.redis = get_redis()
        if self.redis is None:
            raise RedisOperationError("Failed to connect to Redis")
        

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            result = await self.redis.set(key, value, ex=ex)
            return result
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in SET {key}: {e}")
            raise RedisOperationError(f"Failed to set key {key}") from e
        except redis.TimeoutError as e:
            logger.error(f"Redis timeout error in SET {key}: {e}")
            raise RedisOperationError(f"Timeout setting key {key}") from e
        except Exception as e:
            logger.error(f"Unexpected error in SET {key}: {e}")
            raise RedisOperationError(f"Unexpected error setting key {key}") from e

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self.redis.get(key)
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in GET {key}: {e}")
            raise RedisOperationError(f"Failed to get key {key}") from e
        except redis.TimeoutError as e:
            logger.error(f"Redis timeout error in GET {key}: {e}")
            raise RedisOperationError(f"Timeout getting key {key}") from e
        except Exception as e:
            logger.error(f"Unexpected error in GET {key}: {e}")
            raise RedisOperationError(f"Unexpected error getting key {key}") from e

    async def sadd(self, key: str, *values) -> int:
        try:
            return await self.redis.sadd(key, *values)
        except Exception as e:
            logger.error(f"Error in SADD {key}: {e}")
            raise RedisOperationError(f"Failed to add to set {key}") from e

    async def srem(self, key: str, *values) -> int:
        try:
            return await self.redis.srem(key, *values)
        except Exception as e:
            logger.error(f"Error in SREM {key}: {e}")
            raise RedisOperationError(f"Failed to remove from set {key}") from e

    async def smembers(self, key: str) -> set:
        try:
            return await self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Error in SMEMBERS {key}: {e}")
            raise RedisOperationError(f"Failed to get set members {key}") from e

    async def delete(self, *keys) -> int:
        try:
            return await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error in DELETE {keys}: {e}")
            raise RedisOperationError(f"Failed to delete keys {keys}") from e

    def pipeline(self):
        try:
            return self.redis.pipeline()
        except Exception as e:
            logger.error(f"Error creating pipeline: {e}")
            raise RedisOperationError("Failed to create Redis pipeline") from e

    def script(self, lua: str):
        try:
            return self.redis.register_script(lua)
        except Exception as e:
            logger.error(f"Error registering Lua script: {e}")
            raise RedisOperationError("Failed to register Lua script") from e