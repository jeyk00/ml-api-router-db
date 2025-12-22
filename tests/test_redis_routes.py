
def test_redis_route_lifecycle(redis_client):
    """
    Test setting, getting, and deleting a route in Redis.
    Structure: Hash "model_routes" -> key: model_name, value: ip_address
    """
    model_name = "test-model-v1"
    ip_address = "192.168.1.100:8000"
    
    # 1. Set Route
    redis_client.hset("model_routes", model_name, ip_address)
    
    # 2. Get Route
    retrieved_ip = redis_client.hget("model_routes", model_name)
    assert retrieved_ip == ip_address
    
    # 3. Update Route
    new_ip = "192.168.1.101:8000"
    redis_client.hset("model_routes", model_name, new_ip)
    assert redis_client.hget("model_routes", model_name) == new_ip
    
    # 4. Cleanup/Delete
    redis_client.hdel("model_routes", model_name)
    assert redis_client.hget("model_routes", model_name) is None
