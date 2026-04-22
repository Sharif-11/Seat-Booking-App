from contextlib import asynccontextmanager
from app.config.postgres import init_db, close_db
from app.config.redis import init_redis, close_redis
from app.websocket.manager import ws_manager

@asynccontextmanager
async def lifespan(app):
    print("Starting system...")

    await init_db()
    # await init_redis()

    # ws_manager.init()

    yield

    print("Shutting down...")

    await close_redis()
    await close_db()