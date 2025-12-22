import pytest
import redis
import psycopg2
import os

# Configuration (matching docker-compose defaults/env)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = "admin"
POSTGRES_PASSWORD = "secure_password"
POSTGRES_DB = "models_meta"

@pytest.fixture(scope="module")
def redis_client():
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    yield client
    client.close()

@pytest.fixture(scope="module")
def postgres_conn():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB
    )
    conn.autocommit = True
    yield conn
    conn.close()

@pytest.fixture(scope="function")
def postgres_cursor(postgres_conn):
    cur = postgres_conn.cursor()
    yield cur
    cur.close()

@pytest.fixture(autouse=True)
def cleanup_test_data(redis_client, postgres_conn):
    """
    Optional: Clean up specific test keys/rows before/after tests.
    For now, we'll keep it simple and just yield. 
    In a real scenario, we might want to truncate tables or flushdb 
    (but be careful with shared dev DBs!).
    """
    # Setup
    yield
    # Teardown
