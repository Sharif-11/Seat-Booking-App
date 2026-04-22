import psycopg2
from psycopg2.extras import RealDictCursor
from app.config.settings import settings


def get_connection():
    """
    Create a new PostgreSQL connection
    """
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )


def get_cursor():
    """
    Returns connection + dict cursor (recommended for APIs)
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cursor