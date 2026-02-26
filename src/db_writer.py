from typing import Optional
from src.models import MLModelRouting, ModelUsageMetric
from src.database import redis_client, pg_pool

async def register_model(model_data: MLModelRouting):
    """
    (Task: Writer)
    Saves/updates model data in both databases at once.
    Uses connection pooling for efficiency.
    """
    # 1. Write to REDIS (only if an IP address was provided)
    if model_data.ip_address and redis_client:
        # Store in the "model_routes" hash according to the DB structure
        await redis_client.hset(
            "model_routes", 
            key=model_data.model_name, 
            value=model_data.ip_address
        )
        print(f"Saved address {model_data.ip_address} in Redis for {model_data.model_name}")

    # 2. Write/Upsert to POSTGRES
    if pg_pool is not None:
        async with pg_pool.acquire() as conn:
            # Upsert into registry (ON CONFLICT DO UPDATE)
            query = """
                INSERT INTO model_registry (model_name, health_status, last_called_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (model_name) DO UPDATE 
                SET health_status = EXCLUDED.health_status,
                    last_called_at = CURRENT_TIMESTAMP;
            """
            await conn.execute(query, model_data.model_name, model_data.health_status)
            print(f"Updated status for {model_data.model_name} in Postgres")

async def log_model_usage(metric_data: ModelUsageMetric):
    """
    (Task: Writer)
    Logs a model call into the appropriate time bucket in the `model_usage_metrics` table.
    This function is called at the end of each user request.
    """
    if pg_pool is not None:
        async with pg_pool.acquire() as conn:
            query = """
                INSERT INTO model_usage_metrics 
                    (model_name, time_window_start, time_window_end, request_count)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (model_name, time_window_start) DO UPDATE
                SET request_count = model_usage_metrics.request_count + EXCLUDED.request_count;
            """
            
            await conn.execute(
                query,
                metric_data.model_name,
                metric_data.time_window_start,
                metric_data.time_window_end,
                metric_data.request_count
            )
            print(f"Incremented request counter for {metric_data.model_name} "
                  f"in window {metric_data.time_window_start.strftime('%H:%M')} - "
                  f"{metric_data.time_window_end.strftime('%H:%M')}")

async def delete_model(model_name: str):
    """
    (Task: Writer)
    Removes a model from the routing cache (Redis) and from the metadata store (Postgres).
    The cascade delete configured on the fk_model_registry foreign key (ON DELETE CASCADE)
    will automatically take care of removing the associated metrics as well.
    """
    # 1. Remove from REDIS (traffic will stop being routed to it immediately)
    if redis_client:
        deleted_count = await redis_client.hdel("model_routes", model_name)
        if deleted_count > 0:
            print(f"Removed model {model_name} from routing in Redis.")
        else:
            print(f"Model {model_name} did not exist in Redis.")

    # 2. Remove from POSTGRES (hard data and logs)
    if pg_pool is not None:
        async with pg_pool.acquire() as conn:
            query = "DELETE FROM model_registry WHERE model_name = $1"
            result = await conn.execute(query, model_name)
            
            # result comes back as a string like "DELETE 1" or "DELETE 0"
            if result == "DELETE 1":
                print(f"Removed model {model_name} and its associated logs from Postgres.")
            else:
                print(f"Model {model_name} not found in Postgres.")
