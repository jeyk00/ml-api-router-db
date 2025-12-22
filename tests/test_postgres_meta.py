import pytest
import psycopg2
from datetime import datetime

TEST_MODEL_NAME = "test_model_unit_test"

def test_register_model(postgres_cursor):
    """Test registering a new model in the registry."""
    # Cleanup if exists
    postgres_cursor.execute("DELETE FROM model_registry WHERE model_name = %s", (TEST_MODEL_NAME,))
    
    # Register
    postgres_cursor.execute(
        "INSERT INTO model_registry (model_name, health_status, last_called_at) VALUES (%s, %s, NOW())",
        (TEST_MODEL_NAME, 'OK')
    )
    
    # Verify
    postgres_cursor.execute("SELECT model_name, health_status FROM model_registry WHERE model_name = %s", (TEST_MODEL_NAME,))
    row = postgres_cursor.fetchone()
    assert row is not None
    assert row[0] == TEST_MODEL_NAME
    assert row[1] == 'OK'

def test_register_duplicate_model_fails(postgres_cursor):
    """Test that registering a duplicate model name raises an IntegrityError."""
    # Ensure it exists from previous test or create it
    postgres_cursor.execute(
        "INSERT INTO model_registry (model_name) VALUES (%s) ON CONFLICT DO NOTHING",
        (TEST_MODEL_NAME,)
    )
    
    try:
        postgres_cursor.execute(
            "INSERT INTO model_registry (model_name) VALUES (%s)",
            (TEST_MODEL_NAME,)
        )
        pytest.fail("Should have raised IntegrityError for duplicate model name")
    except psycopg2.IntegrityError:
        # Expected
        pass
    except psycopg2.errors.UniqueViolation:
         # Expected (specific PG error)
        pass

def test_time_series_window_upsert_increment(postgres_cursor):
    """
    Critical Test: verification of time series window UPSERT behavior (Increment by 1).
    The user specified that the logic should be "always plus one".
    """
    timestamp = datetime(2025, 1, 1, 12, 0, 0)
    
    # Ensure model exists
    postgres_cursor.execute(
        "INSERT INTO model_registry (model_name) VALUES (%s) ON CONFLICT DO NOTHING",
        (TEST_MODEL_NAME,)
    )
    
    # Clean metrics for this test
    postgres_cursor.execute(
        "DELETE FROM model_usage_metrics WHERE model_name = %s AND time_window = %s",
        (TEST_MODEL_NAME, timestamp)
    )
    
    # 1. First Insert (Initialize with 1)
    # The application logic for a new window is "1 hit".
    upsert_query = """
        INSERT INTO model_usage_metrics (model_name, time_window, request_count)
        VALUES (%s, %s, %s)
        ON CONFLICT (model_name, time_window)
        DO UPDATE SET request_count = model_usage_metrics.request_count + EXCLUDED.request_count;
    """
    
    # First hit
    postgres_cursor.execute(upsert_query, (TEST_MODEL_NAME, timestamp, 1))
    
    # 2. Second Hit (Validating "Plus One")
    postgres_cursor.execute(upsert_query, (TEST_MODEL_NAME, timestamp, 1))
        
    # 3. Verify Aggregation (1 + 1 = 2)
    postgres_cursor.execute(
        "SELECT request_count FROM model_usage_metrics WHERE model_name = %s AND time_window = %s",
        (TEST_MODEL_NAME, timestamp)
    )
    row = postgres_cursor.fetchone()
    assert row is not None
    assert row[0] == 2, f"Expected 2 (1+1), got {row[0]}"
