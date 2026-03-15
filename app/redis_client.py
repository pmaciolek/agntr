import os
import redis.asyncio as redis

# Optionally manage configuration using pydantic-settings in the future
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def get_redis_client():
    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
