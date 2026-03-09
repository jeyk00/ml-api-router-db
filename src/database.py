import os
import asyncpg
import redis.asyncio as redis
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file (useful when running tests locally)
load_dotenv()

# Read env vars the same way docker-compose.yml defines them
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mlapi_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # 'postgres_meta' inside the Docker network
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")      # 'redis_routes' inside the Docker network
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")      # 'redis_routes' inside the Docker network
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Global connection pools — created once when the app starts
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

async def init_db_pools():
    """
    Initializes connection pools for both databases on application startup.
    """
    global pg_pool, redis_client
    
    # 1. PostgreSQL pool
    dsn = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    pg_pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,   # keep at least 1 connection open at all times
        max_size=10   # up to 10 connections in the pool
    )
    print("Connected to PostgreSQL pool.")

    # 2. Redis client (redis.asyncio manages its own connection pool by default)
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        decode_responses=True  # return strings instead of bytes
    )
    print("Connected to Redis.")

async def close_db_pools():
    """
    Closes all connection pools when the server is shutting down.
    """
    global pg_pool, redis_client
    if pg_pool:
        await pg_pool.close()
    if redis_client:
        await redis_client.close()
