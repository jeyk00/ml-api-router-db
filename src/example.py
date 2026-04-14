import asyncio
from pprint import pprint
from datetime import datetime, timedelta
from src.database import init_db_pools, close_db_pools

from src.models import MLModelRouting, ModelUsageMetric, get_window_start

from src.db_writer import (
    register_model, 
    log_model_usage
)

from src.db_reader import (
    get_model_address, 
    get_model,
    get_model_usage
)
async def run_example():
    
    await init_db_pools()
    now = datetime.now()
    example_model_dict = {
        "model_name" : "vesemir",
        "ip_address" : "192.168.1.100",
        "health_status" : "OK",
        "created_at" : now
    }
    example_metrics_dict = {
        "model_name" : "vesemir",
        "time_window_start" : get_window_start(now),
        "time_window_end" : get_window_start(now) + timedelta(minutes=15),
        "request_count" : 42
    }
    
    example_model = MLModelRouting(
        **example_model_dict
    )

    example_metric = ModelUsageMetric(
        **example_metrics_dict
    )

    print("The example model is:")
    pprint(example_model_dict)

    print("The example metrics are:")
    pprint(example_metrics_dict)

    print("\n--- 1. Writing example model to both databases ---")
    await register_model(example_model)

    print("\n--- 2. Writing example metrics to postgres ---")
    await log_model_usage(example_metric)

    print("\n--- 3. Retrieving a model  from the database ---")
    output_address = await get_model_address(example_model_dict["model_name"])
    output_model = await get_model(example_model_dict["model_name"])
    output_model.ip_address = output_address

    print("\n--- 4. Retrieving model metrics from the database ---")
    output_metrics = await get_model_usage(example_model_dict["model_name"], limit=10)

    print("\n--- 5. Output Model Validation---")
    print("address retrieved from REDIS: ", output_address)
    print("output model: ")
    print(output_model)
    print("output metrics: ")
    print(output_metrics)

    # ! BUG metrics are summing when running the script multiple times

    await close_db_pools()

if __name__ == "__main__":
    asyncio.run(run_example())