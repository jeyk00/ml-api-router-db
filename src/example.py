import asyncio
from pprint import pprint
from datetime import datetime, timedelta
from src.database import init_db_pools, close_db_pools

from src.models import MLModelRouting, ModelUsageMetric

from src.db_writer import (
    register_model, 
    log_model_usage
)

from src.db_reader import (
    get_model_address, 
    get_model
)
async def run_example():
    
    await init_db_pools()
    now = datetime.now()
    example_dict = {
        "model_name" : "vesemir",
        "ip_address" : "192.168.1.100",
        "health_status" : "OK",
        "created_at" : now
    }
    
    # Create dummy data using your schemas
    example_model = MLModelRouting(
        **example_dict
    )
    

    example_metric = ModelUsageMetric(
        model_name=example_dict["model_name"],
        time_window_start=now,
        time_window_end=now + timedelta(minutes=15),
        request_count=42
    )
    print("The example is:")
    pprint(example_dict)

    print("\n--- 1. Writing example model to both databases ---")

    await register_model(example_model)

    print("\n--- 2. Writing example metrics to postgres ---")

    await log_model_usage(example_metric)

    print("\n--- 3. Retrieving a model  from the database ---")

    output_address = await get_model_address(example_dict["model_name"])
    output_model = await get_model(example_dict["model_name"])
    output_model.ip_address = output_address

    print("\n--- 4. Output Model ---")
    print("address retrieved from REDIS: ", output_address)
    print(output_model)

    # TODO compare metrics read output !

    await close_db_pools()

if __name__ == "__main__":
    asyncio.run(run_example())