"""Load knowledge base markdown files into database"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.knowledge_loader import load_knowledge_base


async def main():
    force = "--force" in sys.argv
    print(f"Loading knowledge base... (force_reload={force})")
    result = await load_knowledge_base(force_reload=force)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
