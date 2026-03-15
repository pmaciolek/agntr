import os
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis.asyncio as redis

from app.redis_client import get_redis_client

app = FastAPI(title="Agent Hub")

# Ensure static directory exists
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

class ChatMessage(BaseModel):
    message: str

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.get("/api/history")
async def get_history(redis_client: redis.Redis = Depends(get_redis_client)):
    # Retrieve chat history
    history = await redis_client.lrange("chat_history", 0, -1)
    return {"history": history}

@app.post("/api/chat")
async def post_chat(chat: ChatMessage, redis_client: redis.Redis = Depends(get_redis_client)):
    formatted_msg = f"[User] {chat.message}"
    await redis_client.rpush("chat_history", formatted_msg)
    await redis_client.publish("global_chat", chat.message)
    return {"status": "ok"}

@app.get("/health")
async def health_check(redis_client: redis.Redis = Depends(get_redis_client)):
    ping = await redis_client.ping()
    return {"status": "ok", "redis_ping": ping}
