import asyncio
import logging
import os
import json
import redis.asyncio as redis
from openai import AsyncOpenAI

try:
    import wildedge
    we_dsn = os.getenv("WILDEDGE_DSN")
    if we_dsn:
        wildedge_client = wildedge.WildEdge(dsn=we_dsn)
        logger_setup = True
    else:
        wildedge_client = None
except ImportError:
    wildedge_client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisOpenRouterAgent:
    def __init__(self, name: str, markdown_path: str, model: str = "qwen/qwen3.5-flash-02-23"):
        self.name = name
        self.channel_name = f"agent:{self.name}"
        self.global_channel = "global_chat"
        self.model = model
        
        # Load persona and instructions from markdown file
        with open(markdown_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
            
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY is not set. The agent won't be able to communicate with OpenRouter.")
            
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        if wildedge_client:
            self.we_handle = wildedge_client.register_model(
                self.client,
                model_id=self.model,
                source="openrouter",
                auto_instrument=False
            )
        else:
            self.we_handle = None
        
        self.redis = None
        self.pubsub = None
        self.history = [{"role": "system", "content": self.system_prompt}]

    async def connect(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(self.global_channel, self.channel_name)
        logger.info(f"Agent {self.name} connected and subscribed to {self.global_channel} and {self.channel_name}")

    async def start(self):
        await self.connect()
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]
                    
                    if data == "STOP_SYSTEM":
                        logger.info(f"Agent {self.name} received STOP command. Exiting.")
                        break

                    # Avoid processing own messages or basic coordination flags if we prefix them
                    if data.startswith(f"[{self.name}]"):
                        continue
                        
                    await self.process_message(channel, data)
        finally:
            if self.pubsub:
                await self.pubsub.close()
            if self.redis:
                await self.redis.aclose()

    async def process_message(self, channel: str, message: str):
        logger.info(f"Agent {self.name} received message on {channel}: {message}")
        
        self.history.append({"role": "user", "content": message})
        
        try:
            if self.we_handle:
                with wildedge.track(self.we_handle):
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=self.history
                    )
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.history
                )
            reply = response.choices[0].message.content
            
            logger.info(f"Agent {self.name} responding: {reply}")
            
            self.history.append({"role": "assistant", "content": reply})
            
            if "STOP_SYSTEM" in reply:
                logger.info("STOP_SYSTEM triggered by agent.")
                await self.redis.rpush("chat_history", "[System] Simulation STOP_SYSTEM triggered.")
                await self.redis.publish(self.global_channel, "STOP_SYSTEM")
            else:
                formatted_reply = f"[{self.name}] {reply}"
                # Save to history list
                await self.redis.rpush("chat_history", formatted_reply)
                # Publish to pubsub
                await self.redis.publish(self.global_channel, formatted_reply)
                
        except Exception as e:
            logger.error(f"Agent {self.name} error generating response: {e}")

class CoordinatorAgent(RedisOpenRouterAgent):
    async def start_conversation(self, initial_message: str):
        await self.connect()
        logger.info(f"Coordinator starts conversation with: {initial_message}")
        formatted_message = f"[{self.name}] {initial_message}"
        await self.redis.rpush("chat_history", formatted_message)
        await self.redis.publish(self.global_channel, formatted_message)
        await self.start()
