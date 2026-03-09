from typing import Optional
from src.models import MLModelRouting, ModelUsageMetric
from src import database as db


async def get_model_address(model_name: str) -> Optional[str]:
    address = None
    if db.redis_client:
        address = await db.redis_client.hget("model_routes", key=model_name)
    return address

async def get_model(model_name: str) -> Optional[MLModelRouting]:
    if db.pg_pool is not None:
        async with db.pg_pool.acquire() as conn:
            query = """
                SELECT model_name, health_status, last_called_at 
                FROM model_registry 
                WHERE model_name = $1;
            """
            # fetchrow returns a single record (or None if not found)
            record = await conn.fetchrow(query, model_name)
            
            if record:
                # Convert the asyncpg Record object to a standard Python dictionary
                return MLModelRouting(**dict(record))
    return None

async def get_model_usage(model_name: str, limit: int) -> Optional[list[ModelUsageMetric]]:
    if db.pg_pool is not None:
        async with db.pg_pool.acquire() as conn:
            query = """
                SELECT model_name, time_window_start, time_window_end, request_count 
                FROM model_usage_metrics
                WHERE model_name = $1;
                ORDER BY time_window_start
                LIMIT $2
            """
            records = await conn.fetch(query, model_name, limit)
            return [ModelUsageMetric(**dict(record)) for record in records]
    return None


async def get_time_window_usage(time_window_start: str, limit: int) -> Optional[list[ModelUsageMetric]]:
    if db.pg_pool is not None:
        async with db.pg_pool.acquire() as conn:
            query = """
                SELECT model_name, time_window_start, time_window_end, request_count 
                FROM model_usage_metrics
                WHERE time_window_start = $1;
                ORDER BY time_window_start
                LIMIT $2
            """

            records = await conn.fetch(query, time_window_start, limit)
            return [ModelUsageMetric(**dict(record)) for record in records]
    return None