import os
import asyncpg
import redis.asyncio as redis
from typing import Optional
from dotenv import load_dotenv

# Wczytanie zmiennych środowiskowych z pliku .env (jeśli istnieje, np. przy testach)
load_dotenv()

# Pobieranie zmiennych środowiskowych (podobnie jak w docker-compose.yml)
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mlapi_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")  # 'postgres_meta' w sieci dockerowej
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")      # 'redis_routes' w sieci dockerowej
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")      # 'redis_routes' w sieci dockerowej
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Globalne pule połączeń, aby aplikacja tworzyła je raz
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

async def init_db_pools():
    """
    Inicjalizuje pule połączeń do obu baz danych na starcie aplikacji.
    """
    global pg_pool, redis_client
    
    # 1. Pula PostgreSQL
    dsn = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    pg_pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,   # Minimalnie 1 połączenie cały czas otwarte
        max_size=10   # Maksymalnie 10 "słuchawek" w puli
    )
    print("Połączono z pulą PostgreSQL.")

    # 2. Klient Redis (redis.asyncio używa własnej puli połączeń domyślnie)
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        decode_responses=True  # Zwraca stringi zamiast bajtów (wygodniejsze)
    )
    print("Połączono z Redis.")

async def close_db_pools():
    """
    Zamknięcie puli na koniec pracy (np. przy wyłączaniu serwera).
    """
    global pg_pool, redis_client
    if pg_pool:
        await pg_pool.close()
    if redis_client:
        await redis_client.close()
