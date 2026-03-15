import asyncio
import os
import sys

# Ensure the root directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.base import RedisOpenRouterAgent, CoordinatorAgent

async def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: Please set OPENROUTER_API_KEY environment variable.")
        return
        
    bob = RedisOpenRouterAgent(name="Bob", markdown_path="agents/bob.md")
    alice = RedisOpenRouterAgent(name="Alice", markdown_path="agents/alice.md")
    coordinator = CoordinatorAgent(name="Coordinator", markdown_path="agents/coordinator.md")

    # Start all agents concurrently
    task_bob = asyncio.create_task(bob.start())
    task_alice = asyncio.create_task(alice.start())
    task_coord = asyncio.create_task(coordinator.start())

    print("Agents are running... Waiting for user input from Web UI (or STOP_SYSTEM).")
    await asyncio.gather(task_bob, task_alice, task_coord)
    print("Simulation finished.")

if __name__ == "__main__":
    asyncio.run(main())
