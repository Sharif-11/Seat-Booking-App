import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "seat_booking")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")



settings = Settings()