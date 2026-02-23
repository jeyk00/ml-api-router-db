from typing import Optional
from src.models import MLModelRouting, ModelUsageMetric
from src.database import redis_client, pg_pool

async def register_model(model_data: MLModelRouting):
    """
    Zapisuje/Aktualizuje dane modelu w obu bazach naraz.
    Korzysta z puli połączeń dla optymalizacji.
    """
    # 1. Zapis do REDIS (Jeżeli podano IP)
    if model_data.ip_address and redis_client:
        # Zapisujemy do Hasaha "model_routes" zgodnie ze strukturą bazy
        await redis_client.hset(
            "model_routes", 
            key=model_data.model_name, 
            value=model_data.ip_address
        )
        print(f"Zapisano adres {model_data.ip_address} w Redis dla {model_data.model_name}")

    # 2. Zapis/Upsert do POSTGRES
    if pg_pool is not None:
        async with pg_pool.acquire() as conn:
            # Upsert do registry (ON CONFLICT DO UPDATE)
            query = """
                INSERT INTO model_registry (model_name, health_status, last_called_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (model_name) DO UPDATE 
                SET health_status = EXCLUDED.health_status,
                    last_called_at = CURRENT_TIMESTAMP;
            """
            await conn.execute(query, model_data.model_name, model_data.health_status)
            print(f"Zaktualizowano status {model_data.model_name} w Postgres")

async def log_model_usage(metric_data: ModelUsageMetric):
    """
    Loguje wywołanie modelu do odpowiedniego "wiadra" czasowego w tabeli `model_usage_metrics`.
    Ta funkcja jest wołana np. na koniec każdego zapytania od użytkownika.
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
            print(f"Zwiększono licznik żądań dla {metric_data.model_name} "
                  f"dla okna {metric_data.time_window_start.strftime('%H:%M')} - "
                  f"{metric_data.time_window_end.strftime('%H:%M')}")

async def delete_model(model_name: str):
    """
    Usuwa model z pamięci podręcznej rutingu (Redis) oraz z metadanych (Postgres).
    Kaskadowe usuwanie w konfiguracji bazy SQL zadba o usunięcie również powiązanych metryk, 
    ponieważ na kluczu obcym fk_model_registry ustawiono ON DELETE CASCADE.
    """
    # 1. Usunięcie z REDIS (przestaniemy na niego rutować ruch natychmiast)
    if redis_client:
        deleted_count = await redis_client.hdel("model_routes", model_name)
        if deleted_count > 0:
            print(f"Usunięto model {model_name} z rutingu w Redis.")
        else:
            print(f"Model {model_name} nie istniał w Redis.")

    # 2. Usunięcie z POSTGRES (twarde dane i logi)
    if pg_pool is not None:
        async with pg_pool.acquire() as conn:
            query = "DELETE FROM model_registry WHERE model_name = $1"
            result = await conn.execute(query, model_name)
            
            # result zwraca stringa w stylu "DELETE 1" lub "DELETE 0"
            if result == "DELETE 1":
                print(f"Usunięto model {model_name} oraz powiązane logi z Postgres.")
            else:
                print(f"Brak modelu {model_name} w Postgres.")
